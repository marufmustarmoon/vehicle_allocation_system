from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os


MONGO_DB_URL = os.getenv("MONGODB_URL", "mongodb+srv://marufmustarmoon:c5kuYnfrQKyQynTY@marufmustar.q9rok.mongodb.net/?retryWrites=true&w=majority&appName=marufmustar")
print("check url",MONGO_DB_URL)
DATABASE_NAME = "vehicle_allocation_db"

client = None
db = None
allocation_collection = None


async def connect_to_mongo():
    global client, db, allocation_collection ,vehicles_collection,employee_collection # Declare global variables to modify them
    client = AsyncIOMotorClient(MONGO_DB_URL)
    
    try:
        await client.admin.command('ping')
        print("Connected to MongoDB successfully!")
        db = client[DATABASE_NAME]
        print(f"Database selected: {DATABASE_NAME}")
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
        return  # If connection fails, exit the function
    
    # Now set the global variable for allocation_collection
    allocation_collection = db["allocations"]
    vehicles_collection = db["vehicles"]
    employee_collection = db["employees"]
   


async def close_mongo_connection():
    if client:
        client.close()


async def get_allocation_collection():
    
    return allocation_collection  # Return the already initialized collection

async def get_vehicle_collection():
    
    return vehicles_collection


async def get_employee_collection():
    return employee_collection
