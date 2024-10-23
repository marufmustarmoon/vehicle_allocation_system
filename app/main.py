from fastapi import FastAPI
from app.api.v1.allocations import router as allocations_router
from app.database import connect_to_mongo, close_mongo_connection
# from app.redis_cache import cache  # Uncomment when using Redis
from app.config import settings
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load MongoDB connection
    await connect_to_mongo()
    # await cache.init_cache()  # Uncomment when using Redis
    yield
    # Clean up resources
    await close_mongo_connection()
    # await cache.close_cache()  # Uncomment when using Redis

# Create FastAPI instance with lifespan
app = FastAPI(title="Vehicle Allocation System", lifespan=lifespan)

# Include allocation routes
app.include_router(allocations_router, prefix="/api/v1/allocations", tags=["Allocations"])

@app.get("/")
async def read_root():
    return {"app_name": settings.app_name, "debug": settings.debug}
