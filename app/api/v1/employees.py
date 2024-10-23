from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.employee import EmployeeResponse
from app.models.vehicle import Allocation
from app.database import get_allocation_collection,get_employee_collection
from datetime import datetime
from typing import List
from faker import Faker
import random
from datetime import timezone

# from app.redis_cache import cache

router = APIRouter()
fake = Faker()





@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees_with_allocations(
    include_allocations: bool = Query(False, description="Include allocations for each employee"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(10, description="Maximum number of records to return"),
    employee_collection=Depends(get_employee_collection),
    allocation_collection=Depends(get_allocation_collection)
):
    # Fetch employees with pagination
    
    employees = await employee_collection.find().skip(skip).limit(limit).to_list(length=limit)
    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")
    
    employee_with_allocations = []
    current_time = datetime.now(timezone.utc)

    for employee in employees:
        employee_data = EmployeeResponse(
            id=str(employee["_id"]),
            name=employee["name"],
            department=employee["department"],
            allocations=None
        )

        if include_allocations:
            allocation = await allocation_collection.find_one({
                "employee_id": str(employee_data.id),
                "allocation_date": {"$gt": current_time}
            })
            if allocation:
                employee_data.allocated_by = Allocation(
                    id=str(allocation["_id"]),
                    employee_id=allocation["employee_id"],
                    allocation_date=allocation["allocation_date"]
                )

        employee_with_allocations.append(employee_data)

    return employee_with_allocations
           

   


def generate_random_employee() -> dict:
   
    departments = ["HR", "Engineering", "Sales", "Marketing", "Finance", "Operations"]
    
    return {
        "name": fake.name(),
        "department": random.choice(departments),
        
    }

@router.post("/generate-employees")
async def generate_1000_employees(
    employee_collection=Depends(get_employee_collection)  
):
    employees_to_insert = [generate_random_employee() for _ in range(1000)]
    
    try:
        result = await employee_collection.insert_many(employees_to_insert)
        
        return {
            "message": f"Successfully inserted {len(result.inserted_ids)} employees",
            "employee_ids": [str(emp_id) for emp_id in result.inserted_ids]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
