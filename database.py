from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os

class Database:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database = None

    async def connect_to_database(self):
        # MongoDB connection string - you can set this via environment variable
        MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        DATABASE_NAME = os.getenv("DATABASE_NAME", "loginDB")
        
        # Main database for users and claims
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.database = self.client[DATABASE_NAME]
        
        # Initialize collections
        self.hospitals = self.database.hospitals
        self.patients = self.database.patients
        self.insurance_companies = self.database.insurance_companies
        self.claims = self.database.patient_claims  # Claims stored in patient_claims collection in loginDB
        self.hospital_claims = self.database.hospital_claims  # Hospital claims stored in hospital_claims collection
        self.analytics = self.database.analytics  # Analytics data collection
        
        # Create collections dictionary for easy access
        self.collections = {
            "hospital": self.hospitals,
            "patient": self.patients,
            "insurance": self.insurance_companies,
            "claims": self.claims,  # Map claims to the patient_claims collection
            "patient_claims": self.claims,  # Map patient_claims to the claims collection
            "hospital_claims": self.hospital_claims,
            "analytics": self.analytics,
        }
        
        print("Connected to MongoDB.")
        print(f"Main database: {DATABASE_NAME}")
        print(f"Claims collection: patient_claims")
        print("✓ Collections initialized successfully")

    async def close_database_connection(self):
        if self.client:
            self.client.close()
        print("Disconnected from MongoDB.")

# Create a global database instance
db = Database()