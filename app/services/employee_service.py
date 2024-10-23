from bson import ObjectId
from datetime import datetime, timezone
from typing import List
from app.models.employee import EmployeeResponse
from app.models.vehicle import Allocation
from pymongo.collection import Collection
from fastapi import HTTPException
import random
from faker import Faker
from app.redis_cache import cache  # Import your Redis cache instance

fake = Faker()

async def get_employees_with_allocations(
    include_allocations: bool,
    skip: int,
    limit: int,
    employee_collection: Collection,
    allocation_collection: Collection
) -> List[EmployeeResponse]:
    # Check the cache first
    cache_key = f"employees:include_allocations={include_allocations}:skip={skip}:limit={limit}"
    cached_employees = await cache.get(cache_key)

    if cached_employees:
        return [EmployeeResponse(**emp) for emp in cached_employees]

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

    # Cache the result
    await cache.set(cache_key, [emp.dict() for emp in employee_with_allocations], expire=3600)  # Cache for 1 hour

    return employee_with_allocations

def generate_random_employee() -> dict:
    departments = ["HR", "Engineering", "Sales", "Marketing", "Finance", "Operations"]
    return {
        "name": fake.name(),
        "department": random.choice(departments),
    }

async def generate_1000_employees(employee_collection: Collection) -> dict:
    employees_to_insert = [generate_random_employee() for _ in range(1000)]

    try:
        result = await employee_collection.insert_many(employees_to_insert)
        return {
            "message": f"Successfully inserted {len(result.inserted_ids)} employees",
            "employee_ids": [str(emp_id) for emp_id in result.inserted_ids]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
