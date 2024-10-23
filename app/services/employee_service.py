from bson import ObjectId
from datetime import datetime, timezone
from typing import List
from app.models.employee import EmployeeResponse
from app.models.vehicle import Allocation
from pymongo.collection import Collection
from fastapi import HTTPException
import random
from faker import Faker
from app.redis_cache import redis_cache  # Import your redis_cache


fake = Faker()

async def get_employees_with_allocations(
    include_allocations: bool,
    skip: int,
    limit: int,
    employee_collection: Collection,
    allocation_collection: Collection
) -> List[EmployeeResponse]:
    cache_key = f"employees:include_allocations={include_allocations}:skip={skip}:limit={limit}"
    

    cached_employees = await redis_cache.get_cache(cache_key)

    if cached_employees:
        print("Cache hit! Returning cached employees.")
        print(f"Cached data: {cached_employees}")

        if isinstance(cached_employees, str):
            cached_employees = json.loads(cached_employees)

        return [EmployeeResponse(**emp) for emp in cached_employees if isinstance(emp, dict)]

    # print("Cache miss. Fetching employees from the database...")

    # Fetch employees with pagination
    employees = await employee_collection.find().skip(skip).limit(limit).to_list(length=limit)

    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")

    print(f"Fetched employees: {employees}")

    employee_with_allocations = []
    current_time = datetime.now(timezone.utc)

    for employee in employees:
        employee_data = EmployeeResponse(
            id=str(employee["_id"]),
            name = employee["name"],
            department = employee["department"],
            allocated_by=None
           
        )
        if include_allocations:
            try:
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
            except Exception as e:
                print(f"Error fetching allocation for vehicle {employee_data.id}: {e}")

  
        employee_with_allocations.append(employee_data)

    await redis_cache.set_cache(cache_key, [emp.dict() for emp in employee_with_allocations], expire=60)  
    print("Data cached successfully for employee.")

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
        print(f"Inserted {len(result.inserted_ids)} employees into the database.")
        return {
            "message": f"Successfully inserted {len(result.inserted_ids)} employees",
            "employee_ids": [str(emp_id) for emp_id in result.inserted_ids]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
