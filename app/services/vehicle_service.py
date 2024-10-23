from datetime import datetime, timezone
from typing import List
from bson import ObjectId
from app.models.vehicle import VehicleResponse, Allocation
from pymongo.collection import Collection
from fastapi import HTTPException
from faker import Faker
from app.redis_cache import cache  # Import your Redis cache instance

fake = Faker()

async def get_vehicles_with_future_allocations(
    allocated: bool,
    skip: int,
    limit: int,
    vehicle_collection: Collection,
    allocation_collection: Collection
) -> List[VehicleResponse]:
    # Check the cache first
    cache_key = f"vehicles:allocated={allocated}:skip={skip}:limit={limit}"
    cached_vehicles = await cache.get(cache_key)

    if cached_vehicles:
        return [VehicleResponse(**veh) for veh in cached_vehicles]

    # Fetch vehicles with pagination
    vehicles = await vehicle_collection.find().skip(skip).limit(limit).to_list(length=limit)

    if not vehicles:
        raise HTTPException(status_code=404, detail="No vehicles found")

    vehicles_with_allocations = []
    current_time = datetime.now(timezone.utc)

    for vehicle in vehicles:
        vehicle_data = VehicleResponse(
            id=str(vehicle["_id"]),
            model=vehicle["model"],
            plate_number=vehicle["plate_number"],
            driver=vehicle["driver"],
            allocated_by=None
        )

        if allocated:
            allocation = await allocation_collection.find_one({
                "vehicle_id": str(vehicle_data.id),
                "allocation_date": {"$gt": current_time}
            })

            if allocation:
                vehicle_data.allocated_by = Allocation(
                    id=str(allocation["_id"]),
                    employee_id=allocation["employee_id"],
                    allocation_date=allocation["allocation_date"]
                )

        vehicles_with_allocations.append(vehicle_data)

    # Cache the result
    await cache.set(cache_key, [veh.dict() for veh in vehicles_with_allocations], expire=3600)  # Cache for 1 hour

    return vehicles_with_allocations

def generate_random_vehicle() -> dict:
    driver = {
        "name": fake.name(),
        "license_number": fake.license_plate(),
        "contact": fake.phone_number()
    }

    vehicle = {
        "model": fake.word() + " " + fake.word(),  # Example: "Toyota Corolla"
        "plate_number": fake.license_plate(),
        "driver": driver,
        "allocated_by": []
    }

    return vehicle

async def generate_1000_vehicles(vehicle_collection: Collection) -> dict:
    vehicles_to_insert = [generate_random_vehicle() for _ in range(1000)]

    try:
        result = await vehicle_collection.insert_many(vehicles_to_insert)

        return {
            "message": f"Successfully inserted {len(result.inserted_ids)} vehicles",
            "vehicle_ids": [str(vehicle_id) for vehicle_id in result.inserted_ids]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
