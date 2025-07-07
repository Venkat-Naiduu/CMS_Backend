from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from models import ClaimResponse
from services.claims_service import submit_claim, get_patient_claims, get_patient_details, submit_hospital_claim, get_hospital_details, delete_hospital_claim, get_insurance_details, get_analytics, security

router = APIRouter(tags=["Claims"])

@router.post("/patient-claim", response_model=ClaimResponse)
async def submit_patient_claim(
    claimData: str = Form(...),
    documents: List[UploadFile] = File([])
):
    return await submit_claim(claimData, documents)

@router.post("/hospital-claim", response_model=ClaimResponse)
async def submit_hospital_claim_endpoint(
    claimData: str = Form(...),
    documents: List[UploadFile] = File([]),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return await submit_hospital_claim(claimData, documents, credentials)

@router.get("/patient-claims/{patient_id}")
async def get_patient_claims_endpoint(patient_id: str):
    return await get_patient_claims(patient_id)

@router.get("/patient-details")
async def get_patient_details_endpoint(patient_id: str):
    return await get_patient_details(patient_id)

@router.get("/hospital-details")
async def get_hospital_details_endpoint(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None):
    return await get_hospital_details(request, credentials)

@router.delete("/hospital-claim/{claim_id}")
async def delete_hospital_claim_endpoint(claim_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await delete_hospital_claim(claim_id, credentials)

@router.get("/insurance-details")
async def get_insurance_details_endpoint(insurance_name: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_insurance_details(insurance_name, credentials)

@router.get("/analytics")
async def get_analytics_endpoint(insurance_name: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_analytics(insurance_name, credentials)