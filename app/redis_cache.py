from redis import asyncio as aioredis  # Still use asyncio submodule from redis
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field



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
        self.redis = await aioredis.from_url(
            f"redis://{settings.redis.host}:{settings.redis.port}/{settings.redis.db}"
        )

    async def set_cache(self, key: str, value: str, expire: int = 30):
        try:
            await self.redis.set(key, value, ex=expire)  # Use ex for expiration
        except Exception as e:
            print(f"Error setting cache: {e}")

    async def get_cache(self, key: str):
        try:
            return await self.redis.get(key)
        except Exception as e:
            print(f"Error getting cache: {e}")
            return None

    async def delete_cache(self, key: str):
        try:
            await self.redis.delete(key)
        except Exception as e:
            print(f"Error deleting cache: {e}")

    async def close(self):
        if self.redis:
            await self.redis.close()

# Initialize RedisCache globally
redis_cache = RedisCache()

# Lifespan event for FastAPI startup and shutdown
async def on_startup():
    await redis_cache.initialize()

async def on_shutdown():
    await redis_cache.close()
