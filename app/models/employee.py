from pydantic import BaseModel, Field
from typing import  Optional
from datetime import datetime


class Allocation(BaseModel):
    id: str = Field(..., description="Unique identifier of the allocation")
    vehicle_id: str = Field(..., description="Unique identifier of the allocated vehicle")
    allocation_date: datetime 


class Employee(BaseModel):
    name: str = Field(..., description="Name of the employee")
    department: str = Field(..., description="Employee's department")

    class Config:
        from_attributes = True

class EmployeeResponse(BaseModel):
    id: str = Field(..., description="Name of the employee")
    name: str = Field(..., description="Name of the employee")
    department: str = Field(..., description="Employee's department")
    allocated_by: Optional[Allocation] = Field(None, description="Allocation details if any")

   