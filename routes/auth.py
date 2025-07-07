from fastapi import APIRouter
from models import LoginRequest, LoginResponse
from services.auth_service import login_user

router = APIRouter(prefix="/api", tags=["Authentication"])

@router.post("/hospital-login", response_model=LoginResponse)
async def hospital_login(credentials: LoginRequest):
    return await login_user("hospital", credentials)

@router.post("/patient-login", response_model=LoginResponse)
async def patient_login(credentials: LoginRequest):
    return await login_user("patient", credentials)

@router.post("/insurance-login", response_model=LoginResponse)
async def insurance_login(credentials: LoginRequest):
    return await login_user("insurance", credentials) 