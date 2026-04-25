from pydantic_settings import BaseSettings
from typing import List
import os
from pydantic import Field

from zoneinfo import ZoneInfo

KTM_TZ = ZoneInfo("Asia/Kathmandu")

class Settings(BaseSettings):
    # MongoDB configuration
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_DB_NAME: str
    MONGO_HOST: str
    MONGO_PORT: int
    BROKER_URL:str 
    TOKEN_SECRET_KEY:str
    LIVEKIT_API_KEY:str
    LIVEKIT_API_SECRET:str

    MONGO_URI: str = Field(default="", init=False)


    # Redis configuration
    REDIS_URI: str 
    REDIS_CACHE_EXPIRE: int = 300

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ['*']

    # Security / session
    SECRET_KEY: str = "supersecretkey"
    DEBUG: bool = True

    def model_post_init(self, __context=None):
        # Build the Mongo URI after all other fields are loaded
        self.MONGO_URI = f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"
        # self.MONGO_URI = f"mongodb://localhost:{self.MONGO_PORT}"

        # Parse ALLOWED_ORIGINS from env string
        origins = os.getenv("ALLOWED_ORIGINS")
        if origins and isinstance(origins, str):
            self.ALLOWED_ORIGINS = [o.strip() for o in origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
