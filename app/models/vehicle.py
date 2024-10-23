from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Driver Model (Embedded inside Vehicle)
class Driver(BaseModel):
    name: str = Field(..., description="Name of the driver")
    license_number: str = Field(..., description="Driver's license number")
    contact: str = Field(..., description="Driver's contact number")

# Vehicle Model
class Vehicle(BaseModel):
    id: int = Field(..., description="Unique identifier for the vehicle")
    model: str = Field(..., description="Model of the vehicle")
    plate_number: str = Field(..., description="Vehicle's license plate number")
    driver: Driver = Field(..., description="Driver assigned to the vehicle")
    
    # List of allocations (employee_id and allocation_date)
    allocated_by: List[Optional[dict]] = Field(
        [], description="List of allocations with employee_id and allocation_date"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "model": "Toyota Camry",
                "plate_number": "ABC123",
                "driver": {
                    "name": "John Doe",
                    "license_number": "DL123456",
                    "contact": "555-1234"
                },
                "allocated_by": [
                    {
                        "employee_id": 10,
                        "allocation_date": "2024-10-23"
                    }
                ]
            }
        }
