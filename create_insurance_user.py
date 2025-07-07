import asyncio
from database import db
from auth import get_password_hash

async def create_insurance_user():
    try:
        await db.connect_to_database()
        
        # Check if user already exists
        existing_user = await db.collections["insurance"].find_one({"username": "insurance_user"})
        if existing_user:
            print("Insurance user already exists!")
            return
        
        # Create insurance user
        insurance_user = {
            "username": "insurance_user",
            "password": get_password_hash("password123"),
            "insurance_id": "INS-2024-001",
            "insurance_name": "Aetna Health Insurance",
            "email": "insurance@test.com"
        }
        
        result = await db.collections["insurance"].insert_one(insurance_user)
        print(f"Insurance user created successfully with ID: {result.inserted_id}")
        
    except Exception as e:
        print(f"Error creating insurance user: {e}")
    finally:
        await db.close_database_connection()

if __name__ == "__main__":
    asyncio.run(create_insurance_user()) 