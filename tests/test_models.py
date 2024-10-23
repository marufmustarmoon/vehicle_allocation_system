import pytest
from datetime import date, timedelta
from pydantic import ValidationError
from app.models.allocation import AllocationIn

def test_allocation_in_valid():
    allocation = AllocationIn(
        employee_id=1,
        vehicle_id=2,
        allocation_date=date.today() + timedelta(days=1)  # Future date
    )
    assert allocation.employee_id == 1
    assert allocation.vehicle_id == 2

def test_allocation_in_invalid_past_date():
    with pytest.raises(ValidationError):
        AllocationIn(
            employee_id=1,
            vehicle_id=2,
            allocation_date=date.today() - timedelta(days=1)  # Past date
        )

def test_allocation_in_invalid_employee_id():
    with pytest.raises(ValidationError):
        AllocationIn(
            employee_id=0,  # Invalid employee_id (less than 1)
            vehicle_id=2,
            allocation_date=date.today() + timedelta(days=1)
        )
