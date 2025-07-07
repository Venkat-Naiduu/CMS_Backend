from fastapi import APIRouter
from services.health_service import health_check, test_endpoint

router = APIRouter(tags=["Health"])

@router.get("/api/health")
async def health_check_endpoint():
    return await health_check()

@router.get("/api/test")
async def test_endpoint_route():
    return await test_endpoint() 