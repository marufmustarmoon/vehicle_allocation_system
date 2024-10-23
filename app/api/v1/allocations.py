from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.allocation import AllocationIn, AllocationOut, AllocationHistoryFilter,AllocationResponse
from app.database import get_allocation_collection
from bson import ObjectId
from datetime import datetime
from pymongo import ReturnDocument
from typing import List
from faker import Faker

from datetime import timezone


# from app.redis_cache import cache

router = APIRouter()
fake = Faker()




@router.get("/", response_model=List[AllocationResponse])
async def get_allocations(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(10, description="Maximum number of records to return"),
    allocation_collection=Depends(get_allocation_collection)
):
    # Fetch allocations with pagination
    allocations = await allocation_collection.find().skip(skip).limit(limit).to_list(length=limit)

    if not allocations:
        raise HTTPException(status_code=404, detail="No allocations found")
    response_allocations = []

    for allocation in allocations:
        response_allocation = AllocationResponse(
            id=str(allocation["_id"]),
            employee_id=allocation["employee_id"],
            vehicle_id=allocation["vehicle_id"],
            allocation_date=allocation["allocation_date"]
        )
        response_allocations.append(response_allocation) 

    return response_allocations

@router.post("/", response_model=AllocationOut)
async def create_allocation(
    allocation: AllocationIn, 
    allocation_collection=Depends(get_allocation_collection)
):
    # Check if the employee already has any active/future allocation
    future_allocation = await allocation_collection.find_one({
        "employee_id": allocation.employee_id,
        "allocation_date": {"$gte": datetime.now()}
    })
    if future_allocation:
        raise HTTPException(status_code=400, detail="Employee already has a vehicle allocated for a future date")

    # Check if the vehicle is already allocated on the given date
    existing_vehicle_allocation = await allocation_collection.find_one({
        "vehicle_id": allocation.vehicle_id,
        "allocation_date": allocation.allocation_date
    })
    if existing_vehicle_allocation:
        raise HTTPException(status_code=400, detail="Vehicle already allocated on this date")

    # If both checks pass, create the allocation
    result = await allocation_collection.insert_one(allocation.model_dump())
    created_allocation = await allocation_collection.find_one({"_id": result.inserted_id})
    
    return AllocationOut(**created_allocation)


@router.put("/{allocation_id}", response_model=AllocationOut)
async def update_allocation(
    allocation_id: str, 
    allocation: AllocationIn, 
    allocation_collection=Depends(get_allocation_collection)
):
    allocation_id = ObjectId(allocation_id)

    # Prevent updates to past allocations
    if allocation.allocation_date < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Cannot modify past allocations")

    updated_allocation = await allocation_collection.find_one_and_update(
        {"_id": allocation_id},
        {"$set": allocation.model_dump()},
        return_document=ReturnDocument.AFTER
    )
    if not updated_allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return AllocationOut(**updated_allocation)

@router.delete("/{allocation_id}")
async def delete_allocation(allocation_id: str, allocation_collection=Depends(get_allocation_collection)):
    allocation_id = ObjectId(allocation_id)

    allocation = await allocation_collection.find_one({"_id": allocation_id})
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    if allocation["allocation_date"] < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot delete past allocations")

    result = await allocation_collection.delete_one({"_id": allocation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    return {"message": "Allocation deleted successfully"}

@router.get("/history", response_model=List[AllocationResponse])
async def get_allocation_history(
    filters: AllocationHistoryFilter = Depends(), 
    allocation_collection=Depends(get_allocation_collection)
):
    query = {}
    
    # Prepare the query based on the filter criteria
    if filters.employee_id:
        query["employee_id"] = filters.employee_id
    if filters.vehicle_id:
        query["vehicle_id"] = filters.vehicle_id
    if filters.start_date and filters.end_date:
        query["allocation_date"] = {"$gte": filters.start_date, "$lte": filters.end_date}

    # Fetch allocations from the database
    allocations = await allocation_collection.find(query).to_list(1000)

    # Convert allocations to AllocationResponse format
    allocation_out = []
    for allocation in allocations:
        allocation_out.append(AllocationResponse(
            id=str(allocation["_id"]),  # Convert ObjectId to string
            employee_id=allocation["employee_id"],
            vehicle_id=allocation["vehicle_id"],
            allocation_date=allocation["allocation_date"]
        ))

    return allocation_out

