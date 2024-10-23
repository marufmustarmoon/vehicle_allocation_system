from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.allocation import AllocationIn, AllocationOut, AllocationHistoryFilter
from app.database import get_allocation_collection,get_vehicle_collection
from bson import ObjectId
from datetime import datetime
from pymongo import ReturnDocument
from typing import List, Optional


# from app.redis_cache import cache

router = APIRouter()

async def vehicle_collection_dep(vehicle_collection=Depends(get_vehicle_collection)):
    return vehicle_collection

# Dependency injection for MongoDB collection
async def allocation_collection_dep(allocation_collection=Depends(get_allocation_collection)):
    return allocation_collection

@router.post("/", response_model=AllocationOut)
async def create_allocation(
    allocation: AllocationIn, 
    allocation_collection=Depends(allocation_collection_dep)
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
    allocation_collection=Depends(allocation_collection_dep)
):
    allocation_id = ObjectId(allocation_id)

    # Prevent updates to past allocations
    if allocation.allocation_date < datetime.now():
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
async def delete_allocation(allocation_id: str, allocation_collection=Depends(allocation_collection_dep)):
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

@router.get("/history", response_model=List[AllocationOut])
async def get_allocation_history(
    filters: AllocationHistoryFilter = Depends(), 
    allocation_collection=Depends(allocation_collection_dep)
):
    query = {}
    if filters.employee_id:
        query["employee_id"] = filters.employee_id
    if filters.vehicle_id:
        query["vehicle_id"] = filters.vehicle_id
    if filters.start_date and filters.end_date:
        query["allocation_date"] = {"$gte": filters.start_date, "$lte": filters.end_date}

    allocations = await allocation_collection.find(query).to_list(1000)
    allocation_out = [AllocationOut(**allocation) for allocation in allocations]
    return allocation_out



@router.get("/vehicles", response_model=List[dict])
async def get_vehicle_allocations(
    not_allocated: Optional[bool] = Query(None, description="Filter vehicles that are not allocated"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(10, description="Maximum number of records to return"),
    vehicle_collection=Depends(vehicle_collection_dep),
    allocation_collection=Depends(allocation_collection_dep)
):
    pipeline = [
        {
            "$lookup": {
                "from": "allocations",  # the allocation collection
                "localField": "_id",     # vehicle id
                "foreignField": "vehicle_id",  # allocation vehicle id
                "as": "allocations"     # store allocations as a new field
            }
        },
        {
            "$project": {
                "_id": 1,
                "model": 1,
                "plate_number": 1,
                "driver_id": 1,
                "allocated_by": {
                    "$map": {
                        "input": "$allocations",
                        "as": "allocation",
                        "in": {
                            "employee_id": "$$allocation.employee_id",
                            "allocation_date": "$$allocation.allocation_date"
                        }
                    }
                }
            }
        },
        {"$skip": skip},  # Skip the number of records specified by the 'skip' parameter
        {"$limit": limit}  # Limit the number of records returned to the 'limit' parameter
    ]
    
    # If not_allocated filter is set, add match condition to filter vehicles without allocations
    if not_allocated:
        pipeline.append({"$match": {"allocated_by": {"$size": 0}}})

    # Execute the aggregation pipeline
    vehicles = await vehicle_collection.aggregate(pipeline).to_list(1000)

    return vehicles