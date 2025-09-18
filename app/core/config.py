from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # MongoDB configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "growlab"  # default database name

    # Redis configuration
    REDIS_URI: str = "redis://localhost"
    REDIS_CACHE_EXPIRE: int = 300  # cache expiry in seconds

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ["*"]  # change in production

    # Security / session
    SECRET_KEY: str = "supersecretkey"  # for session middleware, JWT, etc.

    DEBUG: bool = True  # toggle debug mode

settings = Settings()
