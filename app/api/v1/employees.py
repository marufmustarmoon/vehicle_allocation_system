from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from app.models.employee import EmployeeResponse
from app.database import get_allocation_collection, get_employee_collection
from app.services.employee_service import (
    get_employees_with_allocations as get_employees_with_allocations_service,
    generate_1000_employees as generate_1000_employees_service
)

router = APIRouter()

@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees_with_allocations(
    include_allocations: bool = Query(False, description="Include allocations for each employee"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(10, description="Maximum number of records to return"),
    employee_collection=Depends(get_employee_collection),
    allocation_collection=Depends(get_allocation_collection)
):
    return await get_employees_with_allocations_service(
        include_allocations,
        skip,
        limit,
        employee_collection,
        allocation_collection
    )

@router.post("/generate-employees")
async def generate_1000_employees(
    employee_collection=Depends(get_employee_collection)
):
    return await generate_1000_employees_service(employee_collection)
