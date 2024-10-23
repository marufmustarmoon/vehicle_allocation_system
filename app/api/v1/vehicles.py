from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.vehicle import VehicleResponse,Allocation
from app.database import get_allocation_collection,get_vehicle_collection
from datetime import datetime
from typing import List, Optional
from faker import Faker
from datetime import timezone




router = APIRouter()
fake = Faker()



@router.get("/vehicles", response_model=List[VehicleResponse])
async def get_vehicles_with_future_allocations(
    not_allocated: Optional[bool] = Query(False, description="Exclude allocation data"),
    skip: int = Query(0, description="Number of vehicles to skip for pagination"),
    limit: int = Query(10, description="Limit number of vehicles to fetch for pagination"),
    vehicle_collection=Depends(get_vehicle_collection),
    allocation_collection=Depends(get_allocation_collection)
):
    
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

        if not_allocated:
            print("Fetching allocations")
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

@router.post("/generate-vehicles")
async def generate_1000_vehicles(
    vehicle_collection=Depends(get_vehicle_collection)
):
    vehicles_to_insert = [generate_random_vehicle() for _ in range(1000)]
    
    try:
        result = await vehicle_collection.insert_many(vehicles_to_insert)

        return {
            "message": f"Successfully inserted {len(result.inserted_ids)} vehicles",
            "vehicle_ids": [str(vehicle_id) for vehicle_id in result.inserted_ids]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

