from passlib.context import CryptContext
import secrets
API_KEY_PREFIX = "hp_" 
API_KEY_LENGTH = 32

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


def generate_api_key() -> str:
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(API_KEY_LENGTH)}"

def hash_api_key(key: str) -> str:
    return pwd_context.hash(key)

def verify_api_key(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

