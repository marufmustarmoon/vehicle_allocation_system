import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Sample data for allocation
new_allocation = {
    "vehicle_id": 123,  # Should be within the range 1 to 1000
    "employee_id": 456,  # Should be within the range 1 to 1000
    "allocation_date": "2024-10-22",
}

def test_create_allocation():
    response = client.post("/api/v1/allocations/", json=new_allocation)
    print(response.json())  # To see the exact validation error
    assert response.status_code == 201
    assert response.json()["vehicle_id"] == new_allocation["vehicle_id"]
    assert response.json()["employee_id"] == new_allocation["employee_id"]

def test_create_duplicate_allocation():
    # First create the allocation
    client.post("/api/v1/allocations/", json=new_allocation)
    # Try to create it again
    response = client.post("/api/v1/allocations/", json=new_allocation)
    print(response.json()) 
    assert response.status_code == 400  # Assuming this is the status code for duplication

def test_create_allocation_with_past_date():
    # Attempt to create an allocation with a past date
    past_allocation = {
        "vehicle_id": 123,
        "employee_id": 456,
        "allocation_date": "2022-10-22",  # A past date
    }
    response = client.post("/api/v1/allocations/", json=past_allocation)
    assert response.status_code == 422
    assert "Allocation date cannot be in the past." in response.json()["detail"][0]["msg"]

def test_create_allocation_with_invalid_vehicle_id():
    # Vehicle ID out of the valid range (greater than 1000)
    invalid_allocation = {
        "vehicle_id": 1500,
        "employee_id": 456,
        "allocation_date": "2024-10-22",
    }
    response = client.post("/api/v1/allocations/", json=invalid_allocation)
    assert response.status_code == 422
    assert "Vehicle ID must be between 1 and 1000." in response.json()["detail"][0]["msg"]

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"app_name": "Vehicle Allocation System", "debug": True}
