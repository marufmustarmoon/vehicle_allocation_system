from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
   
    mongodb_url: str = Field(default="mongodb+srv://marufmustarmoon:c5kuYnfrQKyQynTY@marufmustar.q9rok.mongodb.net/?retryWrites=true&w=majority&appName=marufmustar")  
    mongodb_db: str = "vehicle_allocation_db"  

    app_name: str = "Vehicle Allocation System"
    debug: bool = Field(default=True, env="DEBUG")  

settings = Settings()

print(f"MongoDB URL: {settings.mongodb_url}")
print(f"Debug Mode: {settings.debug}")
