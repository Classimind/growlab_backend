from pydantic_settings import BaseSettings
from typing import List,ClassVar,Optional
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
    DEVICE_TIMEOUT_SEC: int = 300

    # CORS settings
    ALLOWED_ORIGINS: List[str] = ['*']

    MAX_UPLOAD_SIZE: ClassVar[int] = 50 * 1024 * 1024
    CHUNK_SIZE: ClassVar[int] = 1024 * 1024
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    FIRMWARE_ROOT:str = "firmwares"

    # Firebase configuration
    firebase_cred_path: str = Field("hydroponics.json", env="FIREBASE_CRED_PATH")
    firebase_cred_json: Optional[str] = Field(None, env="FIREBASE_CRED_JSON")

    # Security / session
    SECRET_KEY: str = "supersecretkey"
    DEBUG: bool = True

    def model_post_init(self, __context=None):
        # Build the Mongo URI after all other fields are loaded
        # self.MONGO_URI = f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"
        self.MONGO_URI = f"mongodb://localhost:{self.MONGO_PORT}"

        # Parse ALLOWED_ORIGINS from env string
        origins = os.getenv("ALLOWED_ORIGINS")
        if origins and isinstance(origins, str):
            self.ALLOWED_ORIGINS = [o.strip() for o in origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
