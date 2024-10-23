from fastapi import FastAPI
from app.api.v1.allocations import router as allocations_router
from app.api.v1.employees import router as employees_router
from app.api.v1.vehicles import router as vehicles_router
from app.database import connect_to_mongo, close_mongo_connection
from app.redis_cache import redis_cache  # Import Redis cache
from app.config import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load MongoDB connection
    await connect_to_mongo()
    # Initialize Redis cache
    await redis_cache.initialize()
    
    yield

    # Close MongoDB connection
    await close_mongo_connection()
    # Close Redis cache connection
    await redis_cache.close()

# Create FastAPI instance with lifespan
app = FastAPI(title="Vehicle Allocation System", lifespan=lifespan)

# Include allocation, employee, and vehicle routes
app.include_router(allocations_router, prefix="/api/v1/allocations", tags=["Allocations"])
app.include_router(employees_router, prefix="/api/v1", tags=["Employees"])
app.include_router(vehicles_router, prefix="/api/v1", tags=["Vehicles"])

@app.get("/")
async def read_root():
    return {"app_name": settings.app_name, "debug": settings.debug}
