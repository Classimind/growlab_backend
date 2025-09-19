from pydantic_settings import BaseSettings
from typing import List

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
    ALLOWED_ORIGINS: List[str] 

    # Security / session
    SECRET_KEY: str = "supersecretkey"  # for session middleware, JWT, etc.

    DEBUG: bool = True  # toggle debug mode

    # Automatically construct Mongo URI after init
    def __init__(self, **values):
        super().__init__(**values)
        self.MONGO_URI = f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"

    class Config:
        env_file = ".env"  # automatically load .env
        env_file_encoding = "utf-8"


settings = Settings()
