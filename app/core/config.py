from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # MongoDB configuration
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_DB_NAME: str
    MONGO_HOST: str 
    MONGO_PORT: int = 27017

    MONGO_URI: str = None  

    # Redis configuration
    REDIS_URI: str = "redis://localhost"
    REDIS_CACHE_EXPIRE: int = 300  # cache expiry in seconds

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ['*']

    # Security / session
    SECRET_KEY: str = "supersecretkey"

    DEBUG: bool = True

    def __init__(self, **values):
        super().__init__(**values)

        # Construct Mongo URI
        self.MONGO_URI = f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"

        # # Parse ALLOWED_ORIGINS from env if it's a string
        # origins = os.getenv("ALLOWED_ORIGINS")
        # if origins and isinstance(origins, str):
        #     self.ALLOWED_ORIGINS = [origin.strip() for origin in origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
