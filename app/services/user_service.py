from app.models.user import User, Provider
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from typing import Optional
from app.db.clients import mongodb

USER_COLLECTION = "users"

# Use Argon2 for modern, secure password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")



class UserService:
    def __init__(self):
        self.collection = mongodb.db[USER_COLLECTION]
        
    
    async def init_indexes(self):
        await self.collection.create_index("email", unique=True, sparse=True)
        await self.collection.create_index("oauth.provider_user_id", unique=True, sparse=True)

    # -------------------------
    # Password Utilities
    # -------------------------
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    # -------------------------
    # User CRUD Operations
    # -------------------------
    async def add_user(self, userdata: dict):
        """
        Add a new user to the database.
        - Hash password if provider is EMAIL
        - Insert OAuth info as-is for OAuth providers
        - Raise ValueError if duplicate email or OAuth ID exists
        """
        user = User(**userdata)

        # Hash password for email users
        if user.provider == Provider.EMAIL:
            user.password = self.hash_password(user.password)

        data = user.model_dump()
        try:
            await self.collection.insert_one(user.model_dump())
        except DuplicateKeyError as e:
            raise ValueError("User with this email or OAuth ID already exists") from e
        except:
            raise ValueError("Something went wrong")
        # Remove sensitive info before returning
        if "password" in data:
            del data["password"]
        if "oauth" in data and data["oauth"]:
            data["oauth"].pop("access_token", None)
            data["oauth"].pop("refresh_token", None)

        return data

    async def find_user_by_email(self, email: str) -> Optional[dict]:
        return await self.collection.find_one({"email": email})

    async def find_user_by_provider_id(self, provider: Provider, provider_user_id: str) -> Optional[dict]:
        return await self.collection.find_one({
            "provider": provider,
            "oauth.provider_user_id": provider_user_id
        })

    # -------------------------
    # Authentication
    # -------------------------
    async def authenticate_email_user(self, email: str, password: str) -> Optional[dict]:
        """
        Authenticate a user with email and password.
        Returns user data without password if successful, else None.
        """
        user = await self.find_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.get("password", "")):
            return None
        # Remove password before returning
        user.pop("password", None)
        return user

    async def authenticate_oauth_user(self, provider: Provider, provider_user_id: str, access_token: str) -> Optional[dict]:
        """
        Authenticate an OAuth user.
        - Optionally verify access token with provider (not implemented here)
        """
        user =await self.find_user_by_provider_id(provider, provider_user_id)
        if not user:
            return None
        # Remove sensitive info before returning
        if "oauth" in user and user["oauth"]:
            user["oauth"].pop("access_token", None)
            user["oauth"].pop("refresh_token", None)
        return user

