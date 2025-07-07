from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    token: Optional[str] = None

class DocumentInfo(BaseModel):
    name: str
    size: int
    type: str
    lastModified: int

class PatientClaimRequest(BaseModel):
    patientName: str
    patientId: str
    dateOfBirth: str
    phoneNumber: str
    policyNumber: str
    insuranceProvider: str
    claimAmount: str
    treatmentDate: str
    treatmentProvided: str
    diagnosis: str
    hospitalName: str
    hospitalLocation: str
    procedureName: str
    doctorNotes: str
    patientMedicalHistory: str
    itemizedBill: str
    insuranceStartDate: str
    documents: List[DocumentInfo]

class ClaimResponse(BaseModel):
    success: bool
    message: str
    claimId: Optional[str] = None
    errors: Optional[Dict[str, str]] = None