from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os


load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")

class Settings(BaseSettings):
    # MongoDB configuration
    MONGO_URI: str = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    MONGO_DB_NAME: str = MONGO_DB_NAME

    # Redis configuration
    REDIS_URI: str = "redis://localhost"
    REDIS_CACHE_EXPIRE: int = 300  # cache expiry in seconds

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]  # change in production

    # Security / session
    SECRET_KEY: str = "supersecretkey"  # for session middleware, JWT, etc.

    DEBUG: bool = True  # toggle debug mode

settings = Settings()
