class Settings:
    # MongoDB settings
    mongodb_url: str = "mongodb+srv://marufmustarmoon:c5kuYnfrQKyQynTY@marufmustar.q9rok.mongodb.net/?retryWrites=true&w=majority&appName=marufmustar"
    mongodb_db: str = "vehicle_allocation_db"  # Database name can be static or overridden

    # Application settings
    app_name: str = "Vehicle Allocation System"
    debug: bool = True  # Set to False in production

settings = Settings()  # Create an instance of the Settings class
