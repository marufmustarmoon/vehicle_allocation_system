import aioredis
from typing import Optional
from pydantic import BaseSettings, Field

class RedisSettings(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)

class AppSettings(BaseSettings):
    redis: RedisSettings = RedisSettings()

settings = AppSettings()

class RedisCache:
    def __init__(self):
        self.redis = None

    async def initialize(self):
        self.redis = await aioredis.create_redis_pool(
            (settings.redis.host, settings.redis.port),
            db=settings.redis.db
        )

    async def set_cache(self, key: str, value: str, expire: int = 300):
        await self.redis.set(key, value, expire=expire)

    async def get_cache(self, key: str):
        return await self.redis.get(key)

    async def delete_cache(self, key: str):
        await self.redis.delete(key)

    async def close(self):
        self.redis.close()
        await self.redis.wait_closed()

# Initialize RedisCache globally
redis_cache = RedisCache()

# Lifespan event for FastAPI startup and shutdown
async def on_startup():
    await redis_cache.initialize()

async def on_shutdown():
    await redis_cache.close()