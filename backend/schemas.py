from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List, Any

class AuditResult(BaseModel):
    is_compliant: bool
    total_violations: int
    violations: List[Dict[str, Any]]
    compliance_score: float
    summary: str
    approval_status: Optional[str] = None
    status_color: Optional[str] = None

class DocumentResponse(BaseModel):
    id: int
    file_hash: str
    file_type: str
    original_filename: str
    cloudinary_url: str
    groq_response: str
    audit_result: Optional[AuditResult] = None
    created_at: datetime
    is_duplicate: bool = False
    
    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DocumentResponse] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None

class AuditPolicyResponse(BaseModel):
    id: int
    rule_name: str
    rule_type: str
    field_name: str
    condition: str
    expected_value: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True