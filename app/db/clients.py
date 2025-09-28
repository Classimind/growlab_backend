import motor.motor_asyncio
from app.core.config import settings

class MongoDB:
    client: motor.motor_asyncio.AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_db():
    mongodb.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
    mongodb.db = mongodb.client[settings.MONGO_DB_NAME]
    print("MongoDB connected")

async def close_db():
    mongodb.client.close()
    print("MongoDB disconnected")
