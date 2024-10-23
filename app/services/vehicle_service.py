from datetime import datetime, timezone
from typing import List
from bson import ObjectId
from app.models.vehicle import VehicleResponse, Allocation
from pymongo.collection import Collection
from fastapi import HTTPException
from faker import Faker
from app.redis_cache import redis_cache  # Import your redis_cache

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
    print(f"Cache key: {cache_key}")
    
    cached_vehicles = await redis_cache.get_cache(cache_key)

    if cached_vehicles:
        print("Cache hit! Returning cached vehicles.")
        return [VehicleResponse(**veh) for veh in cached_vehicles]

    # print("Cache miss. Fetching vehicles from the database...")

    # Fetch vehicles with pagination
    vehicles = await vehicle_collection.find().skip(skip).limit(limit).to_list(length=limit)
    print(vehicles)
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
            allocated_by=None  # Can be changed to [] if expecting multiple allocations
        )

        if allocated:
            try:
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
            except Exception as e:
                print(f"Error fetching allocation for vehicle {vehicle_data.id}: {e}")

        vehicles_with_allocations.append(vehicle_data)

    # Cache the result
    await redis_cache.set_cache(cache_key, [veh.dict() for veh in vehicles_with_allocations], expire=60)  
    print("Data cached successfully for vehicles.")

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
        print(f"Inserted {len(result.inserted_ids)} vehicles into the database.")
        
        return {
            "message": f"Successfully inserted {len(result.inserted_ids)} vehicles",
            "vehicle_ids": [str(vehicle_id) for vehicle_id in result.inserted_ids]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
