from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.models.vehicle import VehicleResponse
from app.database import get_allocation_collection, get_vehicle_collection
from app.services.vehicle_service import (
    get_vehicles_with_future_allocations as get_vehicles_with_future_allocations_service,
    generate_1000_vehicles as generate_1000_vehicles_service
)

router = APIRouter()

@router.get("/vehicles", response_model=List[VehicleResponse])
async def get_vehicles_with_future_allocations(
    allocated: Optional[bool] = Query(False, description="Exclude allocation data"),
    skip: int = Query(0, description="Number of vehicles to skip for pagination"),
    limit: int = Query(10, description="Limit number of vehicles to fetch for pagination"),
    vehicle_collection=Depends(get_vehicle_collection),
    allocation_collection=Depends(get_allocation_collection)
):
    return await get_vehicles_with_future_allocations_service(
        allocated,
        skip,
        limit,
        vehicle_collection,
        allocation_collection
    )

@router.post("/generate-vehicles")
async def generate_1000_vehicles(
    vehicle_collection=Depends(get_vehicle_collection)
):
    return await generate_1000_vehicles_service(vehicle_collection)
