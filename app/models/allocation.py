from pydantic import BaseModel,ConfigDict, Field, field_validator
from datetime import date, datetime,timezone
import pytz
from typing import Optional
from bson import ObjectId

from pydantic import Field, field_validator

class AllocationIn(BaseModel):
    employee_id: int = Field(..., gt=0, le=1000, description="Employee ID must be between 1 and 1000.")
    vehicle_id: int = Field(..., gt=0, le=1000, description="Vehicle ID must be between 1 and 1000.")
    allocation_date: datetime = Field(..., description="The allocation date must be in the future.")
    
    # @field_validator('allocation_date')
    # def validate_allocation_date(cls, v):
        

    #     if v < datetime.now():
    #         raise ValueError('The allocation date must be in the future.')
    #     return v

   

   

class AllocationOut(BaseModel):
    id: ObjectId = Field(..., alias="_id", description="The allocation ID (ObjectId).")
    employee_id: int
    vehicle_id: int
    allocation_date: datetime

    class Config:
        arbitrary_types_allowed = True  # Allow non-Pydantic types like ObjectId
        json_encoders = {
            ObjectId: lambda v: str(v)  # Converts ObjectId to string for JSON output
        }


   

class AllocationDocument(BaseModel):
    employee_id: int
    vehicle_id: int
    allocation_date: datetime


class AllocationHistoryFilter(BaseModel):
    employee_id: Optional[int] = None
    vehicle_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None