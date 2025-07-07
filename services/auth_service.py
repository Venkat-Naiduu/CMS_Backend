from models import LoginRequest
from auth import verify_password, create_access_token
from utils.database_utils import convert_objectid
from database import db
import traceback

async def login_user(role: str, credentials: LoginRequest):
    try:
        print(f"Login attempt for user: {credentials.username} in role: {role}")
        
        # Find user in the appropriate collection
        user = await db.collections[role].find_one({"username": credentials.username})
        
        if not user:
            print(f"User not found: {credentials.username} in {role} collection")
            return {"success": False, "message": "User not found", "user": None, "token": None}
        
        print(f"User found: {user['username']}")
        
        # Verify password
        if not verify_password(credentials.password, user["password"]):
            print(f"Password verification failed for user: {credentials.username}")
            return {"success": False, "message": "Invalid password", "user": None, "token": None}
        
        print("Password verification successful")
        
        # Create token
        token = create_access_token({"sub": str(user["_id"]), "role": role})
        
        # Prepare user data (remove password, add role, convert ObjectId)
        user_data = user.copy()
        user_data.pop("password", None)  # don't return password
        user_data["role"] = role
        
        # Convert ObjectId to string
        user_data = convert_objectid(user_data)
        
        print(f"Login successful for user: {credentials.username}")
        return {
            "success": True, 
            "message": "Login successful", 
            "user": user_data, 
            "token": token
        }
        
    except Exception as e:
        print(f"Login error: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Login error: {str(e)}", "user": None, "token": None} 