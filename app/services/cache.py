import redis.asyncio as redis_module
from core.config import settings

redis = None  

async def connect_redis():
    global redis
    redis = redis_module.from_url(
        settings.REDIS_URI, encoding="utf-8", decode_responses=True
    )
    # Test connection
    await redis.ping()
    print("Redis connected")

async def close_redis():
    if redis:
        await redis.close()
        print("Redis disconnected")

async def get_cache(key: str):
    if not redis:
        raise RuntimeError("Redis client is not connected")
    return await redis.get(key)

async def set_cache(key: str, value: str, expire: int = None):
    if not redis:
        raise RuntimeError("Redis client is not connected")
    await redis.set(key, value, ex=expire)
