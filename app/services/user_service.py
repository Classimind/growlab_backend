from app.models import user
from app.models.user import User, Provider
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from typing import Optional
from app.db.clients import mongodb
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import HTTPException, status

USER_COLLECTION = "users"

# Use Argon2 for modern, secure password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")



class UserService:
    def __init__(self):
        self.collection = mongodb.db[USER_COLLECTION]

    async def update_fcm_token(self, user_id: str, token: str):
        user = await self.collection.find_one({"_id": ObjectId(user_id) })

        if not user:
            raise Exception("User not found")

        # Skip update if same token
        if user.get("fcm_token") == token:
            return False

        result = await self.collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "fcm_token": token
                }
            }
        )

        return result.modified_count > 0
        
    
    async def init_indexes(self):
        await self.collection.create_index("email", unique=True, sparse=True)
        await self.collection.create_index("oauth.provider_user_id", unique=True, sparse=True)

    # Password Utilities
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def get_user_by_id(self, user_id: str):

        if not ObjectId.is_valid(user_id):
            return None

        user = await self.collection.find_one(
            {"_id": ObjectId(user_id)},
            {
                "password": 0,
                "security": 0,
                "sessions": 0,
                "locked_until":0,
                "failed_login_attempts":0
            }
        )

        if not user:
            return None

        user["_id"] = str(user["_id"])
        return User(**user)
 
    
    async def update_user_profile(self, user_id: str, update_data: dict):

        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id"
            )

        clean_data = {
            k: v for k, v in update_data.items()
            if v is not None
        }

        if not clean_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )

        clean_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "profile.username": clean_data.get("username"),
                    "profile.full_name": clean_data.get("full_name"),
                    "profile.avatar_url": clean_data.get("avatar_url"),
                    "profile.bio": clean_data.get("bio"),
                    "profile.phone_number": clean_data.get("phone_number"),
                    "profile.location": clean_data.get("location"),
                }
            },
            upsert=True
        )
        if result.matched_count == 0:
            return None
        user = await self.get_user_by_id(user_id)
        return user

    # User CRUD Operations
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
          result =   await self.collection.insert_one(user.model_dump())
          data['_id']=result.inserted_id
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
    
    def ensure_utc(self,dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    # Authentication
    async def authenticate_email_user(self, email: str, password: str) -> Optional[dict]:

        user = await self.find_user_by_email(email)

        if not user:
            return None

        #  CHECK ACCOUNT LOCK
        locked_until = self.ensure_utc(user.get("locked_until"))

        if locked_until and locked_until > datetime.now(timezone.utc):
            raise Exception("Account is locked")

    
        #  VERIFY PASSWORD
        if not self.verify_password(password, user.get("password", "")):

            await self.handle_failed_login(user["_id"])
            return None

        #  RESET SECURITY STATE
        await self.reset_failed_attempts(user["_id"])

        # Remove sensitive data
        user.pop("password", None)

        return user
    
    async def handle_failed_login(self, user_id: str):

        user = await self.collection.find_one({"_id": user_id})

        if not user:
            return

        # increment failed attempts
        attempts = user.get("failed_login_attempts", 0) + 1

        update = {
            "failed_login_attempts": attempts
        }

        # lock account after threshold
        MAX_ATTEMPTS = 10
        LOCK_TIME_MINUTES = 30

        if attempts >= MAX_ATTEMPTS:
            update["locked_until"] = datetime.now(timezone.utc) + timedelta(
                minutes=LOCK_TIME_MINUTES
            )

        await self.collection.update_one(
            {"_id": user_id},
            {"$set": update}
        )

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
    
    async def reset_failed_attempts(self, user_id: str):

        await self.collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "failed_login_attempts": 0,
                    "locked_until": None,
                    "last_login": datetime.now(timezone.utc)
                }
            }
        )


