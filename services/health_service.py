from database import db
import traceback

async def health_check():
    return {"status": "healthy"}
 
async def test_endpoint():
    try:
        return {"message": "Test endpoint works", "collections": list(db.collections.keys())}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()} 