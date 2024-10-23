from pydantic import BaseModel, Field

class Employee(BaseModel):
    id: int = Field(..., gt=0, le=1000, description="Employee ID must be between 1 and 1000.")
    name: str = Field(..., description="Name of the employee")
    department: str = Field(..., description="Employee's department")

    class Config:
        orm_mode = True
