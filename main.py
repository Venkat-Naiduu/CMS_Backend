from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
import traceback

# Import routes
from routes import auth, claims, health

app = FastAPI(debug=True)  # Enable debug mode

# Add CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Include OPTIONS for preflight
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.on_event("startup")
async def startup_db_client():
    try:
        await db.connect_to_database()
        print("✓ Database connected successfully")
    except Exception as e:
        print(f"✗ Startup error: {e}")
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_db_client():
    await db.close_database_connection()

# Include routers
app.include_router(auth.router)
app.include_router(claims.router)
app.include_router(health.router)