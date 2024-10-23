from fastapi import APIRouter, Depends, Query
from typing import List
from app.models.allocation import AllocationIn, AllocationOut, AllocationHistoryFilter, AllocationResponse
from app.database import get_allocation_collection
from app.services.allocation_service import (
    get_allocations as get_allocations_service,
    create_allocation as create_allocation_service,
    update_allocation as update_allocation_service,
    delete_allocation as delete_allocation_service,
    get_allocation_history as get_allocation_history_service
)

router = APIRouter()

@router.get("/", response_model=List[AllocationResponse])
async def get_allocations(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(10, description="Maximum number of records to return"),
    allocation_collection=Depends(get_allocation_collection)
):
    return await get_allocations_service(skip, limit, allocation_collection)

@router.post("/", response_model=AllocationOut)
async def create_allocation(
    allocation: AllocationIn,
    allocation_collection=Depends(get_allocation_collection)
):
    return await create_allocation_service(allocation, allocation_collection)

@router.put("/{allocation_id}", response_model=AllocationOut)
async def update_allocation(
    allocation_id: str,
    allocation: AllocationIn,
    allocation_collection=Depends(get_allocation_collection)
):
    return await update_allocation_service(allocation_id, allocation, allocation_collection)

@router.delete("/{allocation_id}")
async def delete_allocation(allocation_id: str, allocation_collection=Depends(get_allocation_collection)):
    return await delete_allocation_service(allocation_id, allocation_collection)

@router.get("/history", response_model=List[AllocationResponse])
async def get_allocation_history(
    filters: AllocationHistoryFilter = Depends(),
    allocation_collection=Depends(get_allocation_collection)
):
    return await get_allocation_history_service(filters, allocation_collection)
