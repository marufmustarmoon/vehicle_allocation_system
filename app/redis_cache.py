# import aioredis

# class RedisCache:
#     def __init__(self):
#         self.redis = None

#     async def init_cache(self):
#         self.redis = await aioredis.create_redis_pool("redis://localhost")

#     async def close_cache(self):
#         if self.redis:
#             self.redis.close()
#             await self.redis.wait_closed()

#     async def set(self, key, value, expire=3600):
#         await self.redis.set(key, value, expire=expire)

#     async def get(self, key):
#         value = await self.redis.get(key)
#         return value

#     async def delete(self, key):
#         await self.redis.delete(key)

# cache = RedisCache()
