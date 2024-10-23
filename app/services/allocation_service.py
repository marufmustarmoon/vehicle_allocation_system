from bson import ObjectId
from datetime import datetime, timezone
from typing import List
from app.models.allocation import AllocationIn, AllocationResponse
from pymongo.collection import Collection
from pymongo import ReturnDocument
from fastapi import HTTPException
from app.redis_cache import redis_cache
import json


# Define a consistent cache key for all allocation-related operations
CACHE_KEY = "allocations"


async def get_allocations(skip: int, limit: int, allocation_collection: Collection) -> List[AllocationResponse]:
    # Cache key for the allocation list
    cache_key = f"{CACHE_KEY}:list:skip={skip}:limit={limit}"
    
    cached_allocations = await redis_cache.get_cache(cache_key)
    
    if cached_allocations:
        
        cached_allocations = json.loads(cached_allocations)
        return [AllocationResponse(**alloc) for alloc in cached_allocations]

    
    
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
            allocation_date=allocation["allocation_date"].isoformat() if isinstance(allocation["allocation_date"], datetime) else allocation["allocation_date"]
        )
        response_allocations.append(response_allocation)

    # Cache the result
    try:
        cache_data = [
            {
                **alloc.dict(),
                "allocation_date": alloc.allocation_date.isoformat()
            } for alloc in response_allocations
        ]
        await redis_cache.set_cache(cache_key, json.dumps(cache_data), expire=60)  
        print("Data cached successfully.")
    except Exception as e:
        print(f"Error setting cache: {e}")

    return response_allocations


async def create_allocation(allocation: AllocationIn, allocation_collection: Collection) -> AllocationResponse:
    # Check if the employee already has any active/future allocation
    future_allocation = await allocation_collection.find_one({
        "employee_id": allocation.employee_id,
        "allocation_date": {"$gte": datetime.now(timezone.utc)}
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

    # Invalidate all allocation caches
    await redis_cache.delete_cache(f"{CACHE_KEY}:*")  
    print("Cache invalidated for allocations after creation.")

    return AllocationResponse(
        id=str(created_allocation["_id"]),
        employee_id=created_allocation["employee_id"],
        vehicle_id=created_allocation["vehicle_id"],
        allocation_date=created_allocation["allocation_date"].isoformat()
    )


async def update_allocation(allocation_id: str, allocation: AllocationIn, allocation_collection: Collection) -> AllocationResponse:
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

    # Invalidate all allocation caches
    await redis_cache.delete_cache(f"{CACHE_KEY}:*")  # Invalidate all allocation-related caches
    print("Cache invalidated for allocations after update.")

    return AllocationResponse(
        id=str(updated_allocation["_id"]),
        employee_id=updated_allocation["employee_id"],
        vehicle_id=updated_allocation["vehicle_id"],
        allocation_date=updated_allocation["allocation_date"].isoformat()
    )


async def delete_allocation(allocation_id: str, allocation_collection: Collection) -> None:
    allocation_id = ObjectId(allocation_id)

    allocation = await allocation_collection.find_one({"_id": allocation_id})
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    if allocation["allocation_date"] < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot delete past allocations")

    result = await allocation_collection.delete_one({"_id": allocation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Allocation not found")

    # Invalidate all allocation caches
    await redis_cache.delete_cache(f"{CACHE_KEY}:*")  # Invalidate all allocation-related caches
    print("Cache invalidated for allocations after deletion.")

    return {"message": "Allocation deleted successfully"}


async def get_allocation_history(filters, allocation_collection: Collection) -> List[AllocationResponse]:
    query = {}

    # Prepare the query based on the filter criteria
    if filters.employee_id:
        query["employee_id"] = filters.employee_id
    if filters.vehicle_id:
        query["vehicle_id"] = filters.vehicle_id
    if filters.start_date and filters.end_date:
        query["allocation_date"] = {"$gte": filters.start_date, "$lte": filters.end_date}

    # Cache key for allocation history
    cache_key = f"{CACHE_KEY}:history:{str(filters)}"
    # print(f"Cache key: {cache_key}")
    
    # Check the cache first
    cached_history = await redis_cache.get_cache(cache_key)

    if cached_history:
        print("Cache hit!")
        return [AllocationResponse(**alloc) for alloc in json.loads(cached_history)]

    # print("Cache miss. Fetching from database...")

    # Fetch allocations from the database
    allocations = await allocation_collection.find(query).to_list(1000)

    # Convert allocations to AllocationResponse format
    allocation_out = []
    for allocation in allocations:
        allocation_out.append(AllocationResponse(
            id=str(allocation["_id"]),
            employee_id=allocation["employee_id"],
            vehicle_id=allocation["vehicle_id"],
            allocation_date=allocation["allocation_date"]
        ))

    # Cache the result
    cache_data = [
        {
            'id': alloc.id,
            'employee_id': alloc.employee_id,
            'vehicle_id': alloc.vehicle_id,
            'allocation_date': alloc.allocation_date.isoformat()
        } for alloc in allocation_out
    ]
    await redis_cache.set_cache(cache_key, json.dumps(cache_data), expire=60)  # Cache for 1 hour
    # print("Data cached successfully.")

    return allocation_out
