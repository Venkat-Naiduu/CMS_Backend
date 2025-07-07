from fastapi import UploadFile, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from models import ClaimResponse
from database import db
from utils.database_utils import convert_objectid
from auth import decode_access_token
from bson import ObjectId
import json
from datetime import datetime
import traceback

security = HTTPBearer()

async def submit_claim(claimData: str, documents: List[UploadFile]):
    try:
        # Parse the claim data
        claim_data = json.loads(claimData)
        
        # Validate required fields
        required_fields = [
            "patientName", "patientId", "dateOfBirth", "phoneNumber",
            "policyNumber", "insuranceProvider", "claimAmount",
            "treatmentDate", "treatmentProvided", "diagnosis",
            "hospitalName", "hospitalLocation", "procedureName", 
            "doctorNotes", "patientMedicalHistory", "itemizedBill", 
            "insuranceStartDate"
        ]
        
        errors = {}
        for field in required_fields:
            if not claim_data.get(field) or str(claim_data.get(field)).strip() == "":
                errors[field] = f"{field.replace('_', ' ').title()} is required"
        
        if errors:
            return ClaimResponse(
                success=False,
                message="Validation error",
                errors=errors
            )
        
        # Validate file sizes (500KB limit)
        max_file_size = 500 * 1024  # 500KB
        for file in documents:
            if file.size > max_file_size:
                return ClaimResponse(
                    success=False,
                    message=f"File {file.filename} exceeds 500KB limit"
                )
        
        # Validate file types
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'text/plain']
        for file in documents:
            if file.content_type not in allowed_types:
                return ClaimResponse(
                    success=False,
                    message=f"File {file.filename} has invalid type. Only PDF, JPG, PNG, and TXT files are allowed"
                )
        
        # Save files (in a real app, you'd save to cloud storage)
        saved_files = []
        for file in documents:
            # For demo purposes, just store file info
            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            saved_files.append(file_info)
        
        # Generate claim ID based on patient ID and date with sequential number
        current_date = datetime.utcnow()
        base_claim_id = f"{claim_data['patientId']}{current_date.strftime('%m%d%Y')}"
        
        # Check if there are existing claims for this patient on the same day
        existing_claims = await db.collections["claims"].find({
            "patientId": claim_data["patientId"],
            "claimId": {"$regex": f"^{claim_data['patientId']}{current_date.strftime('%m%d%Y')}"}
        }).to_list(length=100)
        
        if existing_claims:
            # Add sequential number
            claim_id = f"{base_claim_id}{len(existing_claims) + 1}"
        else:
            claim_id = base_claim_id
        
        # Create claim document
        claim_document = {
            "patientName": claim_data["patientName"],
            "patientId": claim_data["patientId"],
            "dateOfBirth": claim_data["dateOfBirth"],
            "phoneNumber": claim_data["phoneNumber"],
            "policyNumber": claim_data["policyNumber"],
            "insuranceProvider": claim_data["insuranceProvider"],
            "claimAmount": claim_data["claimAmount"],
            "treatmentDate": claim_data["treatmentDate"],
            "treatmentProvided": claim_data["treatmentProvided"],
            "diagnosis": claim_data["diagnosis"],
            "hospitalName": claim_data["hospitalName"],
            "hospitalLocation": claim_data["hospitalLocation"],
            "procedureName": claim_data["procedureName"],
            "doctorNotes": claim_data["doctorNotes"],
            "patientMedicalHistory": claim_data["patientMedicalHistory"],
            "itemizedBill": claim_data["itemizedBill"],
            "insuranceStartDate": claim_data["insuranceStartDate"],
            "documents": saved_files,
            "status": "pending",
            "submittedAt": datetime.utcnow(),
            "claimId": claim_id
        }
        
        # Save to database
        result = await db.collections["claims"].insert_one(claim_document)
        
        return ClaimResponse(
            success=True,
            message="Claim submitted successfully",
            claimId=claim_id
        )
        
    except json.JSONDecodeError:
        return ClaimResponse(
            success=False,
            message="Invalid JSON data in claimData"
        )
    except Exception as e:
        print(f"Error submitting claim: {e}")
        traceback.print_exc()
        return ClaimResponse(
            success=False,
            message=f"Error submitting claim: {str(e)}"
        )

async def get_patient_claims(patient_id: str):
    try:
        claims = await db.collections["claims"].find({"patientId": patient_id}).to_list(length=100)
        claims = [convert_objectid(claim) for claim in claims]
        return {"success": True, "claims": claims}
    except Exception as e:
        return {"success": False, "message": str(e)}

async def get_patient_details(patient_id: str):
    """
    Get patient details with claims formatted for the frontend dashboard.
    Returns claims in the specific format expected by the UI.
    """
    try:
        print(f"Fetching claims for patient_id: {patient_id}")
        
        # Find claims for the patient
        claims = await db.collections["claims"].find({"patientId": patient_id}).to_list(length=100)
        
        print(f"Found {len(claims)} claims for patient {patient_id}")
        
        if not claims:
            print(f"No claims found for patient {patient_id}")
            return {"success": False, "message": "Patient not found"}
        
        # Format claims for the frontend
        formatted_claims = []
        for i, claim in enumerate(claims):
            print(f"Processing claim {i+1}: {claim.get('claimId', 'No claimId')}")
            formatted_claim = {
                "date": claim.get("treatmentDate", ""),  # Date of treatment
                "provider": claim.get("insuranceProvider", ""),  # Insurance provider
                "service": claim.get("procedureName", claim.get("treatmentProvided", "")),  # Procedure name or treatment provided
                "amount": f"${claim.get('claimAmount', '0')}",  # Formatted amount
                "status": claim.get("status", "pending"),  # Claim status
                "claimNumber": claim.get("claimId", ""),  # Unique claim number
                "hospitalName": claim.get("hospitalName", ""),  # Hospital name
                "diagnosis": claim.get("diagnosis", "")  # Diagnosis
            }
            formatted_claims.append(formatted_claim)
            print(f"Formatted claim {i+1}: {formatted_claim}")
        
        print(f"Returning {len(formatted_claims)} formatted claims")
        return {
            "claims": formatted_claims
        }
        
    except Exception as e:
        print(f"Error fetching patient details: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Error fetching patient details: {str(e)}"}

async def submit_hospital_claim(claimData: str, documents: List[UploadFile], credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Verify JWT token and get hospital_id
        token = credentials.credentials
        payload = decode_access_token(token)
        hospital_object_id = payload.get("sub")  # This is the hospital's MongoDB _id from login
        
        if not hospital_object_id:
            return ClaimResponse(
                success=False,
                message="Invalid token or hospital not found"
            )
        
        # Get the actual hospital ID (like HOSP1) from the database
        hospital = await db.collections["hospital"].find_one({"_id": ObjectId(hospital_object_id)})
        if not hospital:
            return ClaimResponse(
                success=False,
                message="Hospital not found"
            )
        
        hospital_id = hospital.get("hospitalid", "HOSP1")  # Get the actual hospital ID like HOSP1 (note: lowercase 'hospitalid')
        
        # Parse the claim data
        claim_data = json.loads(claimData)
        
        # Validate required fields
        required_fields = [
            "patientName", "patientId", "dateOfBirth", "phoneNumber",
            "policyNumber", "insuranceProvider", "claimAmount",
            "treatmentDate", "treatmentProvided", "diagnosis",
            "hospitalName", "hospitalLocation", "procedureName", 
            "doctorNotes", "patientMedicalHistory", "itemizedBill", 
            "insuranceStartDate"
        ]
        
        errors = {}
        for field in required_fields:
            if not claim_data.get(field) or str(claim_data.get(field)).strip() == "":
                errors[field] = f"{field.replace('_', ' ').title()} is required"
        
        if errors:
            return ClaimResponse(
                success=False,
                message="Validation error",
                errors=errors
            )
        
        # Validate file sizes (500KB limit)
        max_file_size = 500 * 1024  # 500KB
        for file in documents:
            if file.size > max_file_size:
                return ClaimResponse(
                    success=False,
                    message=f"File {file.filename} exceeds 500KB limit"
                )
        
        # Validate file types
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'text/plain']
        for file in documents:
            if file.content_type not in allowed_types:
                return ClaimResponse(
                    success=False,
                    message=f"File {file.filename} has invalid type. Only PDF, JPG, PNG, and TXT files are allowed"
                )
        
        # Save files (in a real app, you'd save to cloud storage)
        saved_files = []
        for file in documents:
            # For demo purposes, just store file info
            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            saved_files.append(file_info)
        
        # Generate claim ID based on hospital ID and date with sequential number
        current_date = datetime.utcnow()
        base_claim_id = f"{hospital_id}{current_date.strftime('%m%d%Y')}"
        
        # Check if there are existing claims for this hospital on the same day
        existing_claims = await db.collections["hospital_claims"].find({
            "hospitalId": hospital_id,
            "claimId": {"$regex": f"^{hospital_id}{current_date.strftime('%m%d%Y')}"}
        }).to_list(length=100)
        
        if existing_claims:
            # Add sequential number
            claim_id = f"{base_claim_id}{len(existing_claims) + 1}"
        else:
            claim_id = base_claim_id
        
        # Create claim document
        claim_document = {
            "hospitalId": hospital_id,  # Add actual hospital ID (like HOSP1)
            "hospitalObjectId": hospital_object_id,  # Add MongoDB ObjectId for reference
            "patientName": claim_data["patientName"],
            "patientId": claim_data["patientId"],
            "dateOfBirth": claim_data["dateOfBirth"],
            "phoneNumber": claim_data["phoneNumber"],
            "policyNumber": claim_data["policyNumber"],
            "insuranceProvider": claim_data["insuranceProvider"],
            "claimAmount": claim_data["claimAmount"],
            "treatmentDate": claim_data["treatmentDate"],
            "treatmentProvided": claim_data["treatmentProvided"],
            "diagnosis": claim_data["diagnosis"],
            "hospitalName": claim_data["hospitalName"],
            "hospitalLocation": claim_data["hospitalLocation"],
            "procedureName": claim_data["procedureName"],
            "doctorNotes": claim_data["doctorNotes"],
            "patientMedicalHistory": claim_data["patientMedicalHistory"],
            "itemizedBill": claim_data["itemizedBill"],
            "insuranceStartDate": claim_data["insuranceStartDate"],
            "documents": saved_files,
            "status": "pending",
            "submittedAt": datetime.utcnow(),
            "claimId": claim_id
        }
        
        # Save to hospital_claims collection
        result = await db.collections["hospital_claims"].insert_one(claim_document)
        
        return ClaimResponse(
            success=True,
            message="Hospital claim submitted successfully",
            claimId=claim_id
        )
        
    except json.JSONDecodeError:
        return ClaimResponse(
            success=False,
            message="Invalid JSON data in claimData"
        )
    except Exception as e:
        print(f"Error submitting hospital claim: {e}")
        traceback.print_exc()
        return ClaimResponse(
            success=False,
            message=f"Error submitting hospital claim: {str(e)}"
        )

async def get_hospital_details(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Get hospital details with claims formatted for the hospital dashboard.
    Returns claims in the specific format expected by the UI.
    Supports both JWT and ?hospitalid=... query param.
    """
    try:
        # Try to get hospitalid from query param first
        hospital_id = request.query_params.get("hospitalid")
        if hospital_id:
            print(f"Using hospitalid from query param: {hospital_id}")
        else:
            # Fallback to JWT token
            token = credentials.credentials if credentials else None
            payload = decode_access_token(token) if token else None
            if not payload:
                return {"success": False, "message": "Invalid or expired token"}
            hospital_object_id = payload.get("sub")
            if not hospital_object_id:
                return {"success": False, "message": "Invalid token or hospital not found"}
            hospital = await db.collections["hospital"].find_one({"_id": ObjectId(hospital_object_id)})
            if not hospital:
                return {"success": False, "message": "Hospital not found"}
            hospital_id = hospital.get("hospitalid", "HOSP1")
            print(f"Using hospitalid from JWT: {hospital_id}")
        
        # Find claims for the hospital
        claims = await db.collections["hospital_claims"].find({"hospitalId": hospital_id}).to_list(length=100)
        print(f"Found {len(claims)} claims for hospital {hospital_id}")
        if not claims:
            print(f"No claims found for hospital {hospital_id}")
            return {"claims": []}
        # Format claims for the frontend (only required fields)
        formatted_claims = []
        for i, claim in enumerate(claims):
            try:
                print(f"Processing claim {i+1}: {claim.get('claimId', 'No claimId')}")
                submitted_at = claim.get("submittedAt")
                submission_date = ""
                if submitted_at:
                    if isinstance(submitted_at, datetime):
                        submission_date = submitted_at.strftime("%Y-%m-%d")
                    elif isinstance(submitted_at, str):
                        try:
                            parsed_date = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                            submission_date = parsed_date.strftime("%Y-%m-%d")
                        except:
                            submission_date = submitted_at[:10] if len(submitted_at) >= 10 else submitted_at
                    else:
                        submission_date = str(submitted_at)[:10] if str(submitted_at) else ""
                formatted_claim = {
                    "id": claim.get("claimId", ""),
                    "patientName": claim.get("patientName", ""),
                    "submissionDate": submission_date,
                    "amount": f"${claim.get('claimAmount', '0')}",
                    "status": "In Progress" if claim.get("status", "pending") == "pending" else claim.get("status", "pending")
                }
                formatted_claims.append(formatted_claim)
                print(f"Formatted claim {i+1}: {formatted_claim}")
            except Exception as claim_error:
                print(f"Error processing claim {i+1}: {claim_error}")
                continue
        print(f"Returning {len(formatted_claims)} formatted claims")
        return {
            "claims": formatted_claims
        }
    except Exception as e:
        print(f"Error fetching hospital details: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Error fetching hospital details: {str(e)}"}

async def delete_hospital_claim(claim_id: str, credentials: HTTPAuthorizationCredentials):
    """
    Delete a hospital claim by claim ID.
    """
    try:
        # Verify JWT token and get hospital_id
        token = credentials.credentials
        payload = decode_access_token(token)
        hospital_object_id = payload.get("sub")  # This is the hospital's MongoDB _id from login
        
        if not hospital_object_id:
            return {"success": False, "message": "Invalid token or hospital not found"}
        
        # Get the actual hospital ID (like HOSP1) from the database
        hospital = await db.collections["hospital"].find_one({"_id": ObjectId(hospital_object_id)})
        if not hospital:
            return {"success": False, "message": "Hospital not found"}
        
        hospital_id = hospital.get("hospitalid", "HOSP1")  # Get the actual hospital ID like HOSP1 (note: lowercase 'hospitalid')
        
        print(f"Attempting to delete claim {claim_id} for hospital {hospital_id}")
        
        # Find and delete the claim (only if it belongs to this hospital)
        result = await db.collections["hospital_claims"].delete_one({
            "claimId": claim_id,
            "hospitalId": hospital_id
        })
        
        if result.deleted_count == 0:
            return {"success": False, "message": "Claim not found or not authorized to delete"}
        
        print(f"Successfully deleted claim {claim_id}")
        return {
            "success": True,
            "message": f"Claim {claim_id} deleted successfully"
        }
        
    except Exception as e:
        print(f"Error deleting hospital claim: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Error deleting claim: {str(e)}"}

async def get_insurance_details(insurance_name: str, credentials: HTTPAuthorizationCredentials):
    """
    Get insurance details with claims from both patient_claims and hospital_claims collections.
    Filters claims where insuranceProvider matches the provided insurance_name.
    """
    try:
        # Verify JWT token
        token = credentials.credentials
        print(f"Token received: {token[:50]}...")  # Debug: show first 50 chars of token
        
        payload = decode_access_token(token)
        print(f"Token payload: {payload}")  # Debug: show decoded payload
        
        if not payload:
            return {"success": False, "message": "Invalid token or insurance user not found"}
        
        # Check if user has insurance role
        user_role = payload.get("role")
        if user_role != "insurance":
            return {"success": False, "message": f"Access denied. User role is {user_role}, expected insurance"}
        
        print(f"Fetching claims for insurance provider: {insurance_name}")
        
        # Get claims from patient_claims collection
        patient_claims = await db.collections["patient_claims"].find({
            "insuranceProvider": insurance_name
        }).to_list(length=100)
        
        # Get claims from hospital_claims collection
        hospital_claims = await db.collections["hospital_claims"].find({
            "insuranceProvider": insurance_name
        }).to_list(length=100)
        
        print(f"Found {len(patient_claims)} patient claims and {len(hospital_claims)} hospital claims")
        
        # Combine and format all claims
        all_claims = []
        
        # Process patient claims
        for claim in patient_claims:
            try:
                submitted_at = claim.get("submittedAt")
                submission_date = ""
                if submitted_at:
                    if isinstance(submitted_at, datetime):
                        submission_date = submitted_at.strftime("%Y-%m-%d")
                    elif isinstance(submitted_at, str):
                        try:
                            parsed_date = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                            submission_date = parsed_date.strftime("%Y-%m-%d")
                        except:
                            submission_date = submitted_at[:10] if len(submitted_at) >= 10 else submitted_at
                    else:
                        submission_date = str(submitted_at)[:10] if str(submitted_at) else ""
                
                formatted_claim = {
                    "claimId": claim.get("claimId", ""),
                    "patientName": claim.get("patientName", ""),
                    "submissionDate": submission_date,
                    "amount": f"${claim.get('claimAmount', '0')}",
                    "status": "In Progress" if claim.get("status", "pending") == "pending" else claim.get("status", "pending"),
                    "source": "patient"
                }
                all_claims.append(formatted_claim)
            except Exception as claim_error:
                print(f"Error processing patient claim: {claim_error}")
                continue
        
        # Process hospital claims
        for claim in hospital_claims:
            try:
                submitted_at = claim.get("submittedAt")
                submission_date = ""
                if submitted_at:
                    if isinstance(submitted_at, datetime):
                        submission_date = submitted_at.strftime("%Y-%m-%d")
                    elif isinstance(submitted_at, str):
                        try:
                            parsed_date = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                            submission_date = parsed_date.strftime("%Y-%m-%d")
                        except:
                            submission_date = submitted_at[:10] if len(submitted_at) >= 10 else submitted_at
                    else:
                        submission_date = str(submitted_at)[:10] if str(submitted_at) else ""
                
                formatted_claim = {
                    "claimId": claim.get("claimId", ""),
                    "patientName": claim.get("patientName", ""),
                    "submissionDate": submission_date,
                    "amount": f"${claim.get('claimAmount', '0')}",
                    "status": "In Progress" if claim.get("status", "pending") == "pending" else claim.get("status", "pending"),
                    "source": "hospital"
                }
                all_claims.append(formatted_claim)
            except Exception as claim_error:
                print(f"Error processing hospital claim: {claim_error}")
                continue
        
        # Sort by submission date (newest first)
        all_claims.sort(key=lambda x: x["submissionDate"], reverse=True)
        
        print(f"Returning {len(all_claims)} total claims for insurance provider {insurance_name}")
        return {
            "success": True,
            "insurance_name": insurance_name,
            "claims": all_claims
        }
        
    except Exception as e:
        print(f"Error fetching insurance details: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Error fetching insurance details: {str(e)}"}

async def get_analytics(insurance_name: str, credentials: HTTPAuthorizationCredentials):
    """
    Get analytics data for insurance provider using provided insurance_name.
    """
    try:
        # Verify JWT token
        token = credentials.credentials
        payload = decode_access_token(token)
        if not payload:
            return {"success": False, "message": "Invalid token or insurance user not found"}
        
        # Check if user has insurance role
        user_role = payload.get("role")
        if user_role != "insurance":
            return {"success": False, "message": f"Access denied. User role is {user_role}, expected insurance"}
        
        print(f"Fetching analytics for insurance provider: {insurance_name}")
        
        # Get all analytics data for this insurance provider
        analytics_data = await db.collections["analytics"].find({
            "insuranceProvider": insurance_name
        }).to_list(length=1000)
        
        # Convert ObjectId to string for JSON serialization
        from utils.database_utils import convert_objectid
        for item in analytics_data:
            convert_objectid(item)
        
        print(f"Found {len(analytics_data)} analytics records for insurance provider {insurance_name}")
        
        # Get severity distribution
        severity_distribution = await db.collections["analytics"].aggregate([
            {"$match": {"insuranceProvider": insurance_name}},
            {"$group": {
                "_id": "$severity",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]).to_list(length=10)
        
        # Format severity distribution
        severity_stats = {}
        for item in severity_distribution:
            severity_stats[item["_id"]] = item["count"]
        
        return {
            "success": True,
            "insurance_name": insurance_name,
            "claims": analytics_data,
            "severity_distribution": severity_stats
        }
        
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        traceback.print_exc()
        return {"success": False, "message": f"Error fetching analytics: {str(e)}"} 