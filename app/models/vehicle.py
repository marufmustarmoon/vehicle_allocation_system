from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Driver(BaseModel):
    name: str = Field(..., description="Name of the driver")
    license_number: str = Field(..., description="Driver's license number")
    contact: str = Field(..., description="Driver's contact number")

class Allocation(BaseModel):
    id: str = Field(..., description="Unique identifier of the allocation")
    employee_id: str = Field(..., description="Unique identifier of the employee who allocated the vehicle")
    allocation_date: datetime 

class Vehicle(BaseModel):
    model: str = Field(..., description="Model of the vehicle")
    plate_number: str = Field(..., description="Vehicle's license plate number")
    driver: Driver = Field(..., description="Driver assigned to the vehicle")
    
    # Change allocated_by to a single Allocation object
    allocated_by: Optional[Allocation] = Field(
        None, description="Allocation details if any"
    )
    
    class Config:
        json_schema_extra = { 
            "example": {
                "id": "603e9b8b2f1e8d2b5a123456",
                "model": "Toyota Camry",
                "plate_number": "ABC123",
                "driver": {
                    "name": "John Doe",
                    "license_number": "DL123456",
                    "contact": "555-1234"
                },
                "allocated_by": {
                    "employee_id": "10",
                    "allocation_date": "2024-10-23T12:00:00Z"
                }
            }
        }

class VehicleResponse(BaseModel):
    id: str = Field(..., description="Unique identifier of the vehicle")
    model: str = Field(..., description="Model of the vehicle")
    plate_number: str = Field(..., description="Vehicle's license plate number")
    allocated_by: Optional[Allocation] = Field(None, description="Allocation details if any")
