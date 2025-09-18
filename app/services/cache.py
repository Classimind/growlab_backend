import aioredis
from app.core.config import settings

redis = None

async def connect_redis():
    global redis
    redis = await aioredis.from_url(
        settings.REDIS_URI, encoding="utf8", decode_responses=True
    )
    print("Redis connected")

async def close_redis():
    await redis.close()
    print("Redis disconnected")

async def get_cache(key: str):
    return await redis.get(key)

async def set_cache(key: str, value: str, expire: int = None):
    await redis.set(key, value, ex=expire)
