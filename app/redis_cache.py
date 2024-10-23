import aioredis
from app.core.config import settings

redis_client = None

async def connect_to_redis():
    global redis_client
    redis_client = await aioredis.create_redis_pool(settings.redis_url)

async def close_redis_connection():
    redis_client.close()
    await redis_client.wait_closed()

async def get_cached_data(key: str):
    value = await redis_client.get(key)
    if value:
        return value.decode('utf-8')
    return None

async def set_cache_data(key: str, value: str, ttl: int = 300):
    await redis_client.set(key, value, expire=ttl)

async def delete_cache_data(key: str):
    await redis_client.delete(key)
