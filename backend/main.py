from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

from database import get_db, engine
from models import Base, Document, AuditPolicy, AuditRule
from schemas import DocumentResponse, UploadResponse, ErrorResponse, AuditPolicyResponse
from utils import (
    generate_file_hash,
    detect_file_type,
    upload_to_cloudinary,
    process_with_groq
)
from audit_service import create_default_audit_policies, create_default_audit_rules, perform_audit
from config import settings
from migrate import migrate_database

# Create tables
Base.metadata.create_all(bind=engine)

# Run migration
migrate_database()

# Initialize default audit policies and rules
with next(get_db()) as db:
    create_default_audit_policies(db)
    create_default_audit_rules(db)

app = FastAPI(title="Document Processing API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=4)

@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Validate file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Validate file extension
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Generate hash and check for duplicates
        file_hash = generate_file_hash(file_content)
        
        try:
            existing_doc = db.query(Document).filter(Document.file_hash == file_hash).first()
        except Exception as db_error:
            # Handle database connection issues
            db.rollback()
            existing_doc = None
        
        if existing_doc:
            raise HTTPException(
                status_code=400, 
                detail=f"Duplicate flagged and cant upload again|📄 {existing_doc.original_filename}|🕒 {existing_doc.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # Detect file type
        file_type, is_processable = detect_file_type(file_content, file.filename)
        
        if not is_processable:
            raise HTTPException(status_code=400, detail="File cannot be processed")
        
        # Process in parallel: upload to cloudinary and process with groq
        loop = asyncio.get_event_loop()
        
        groq_task = loop.run_in_executor(
            executor,
            process_with_groq,
            file_content,
            file_type,
            file.filename
        )
        
        # Get Groq response first to check if it's an invoice
        groq_response, json_data = await groq_task
        
        # Check if document is an invoice
        content = groq_response.lower()
        invoice_keywords = ['invoice', 'bill', 'receipt', 'total', 'amount', 'price', 'cost', 'payment']
        has_invoice_format = any(keyword in content for keyword in invoice_keywords)
        
        if not has_invoice_format:
            raise HTTPException(
                status_code=400, 
                detail="Document rejected: Only invoice/bill documents are accepted for processing."
            )
        
        # Only upload to Cloudinary if it's an invoice
        upload_task = loop.run_in_executor(
            executor,
            upload_to_cloudinary,
            file_content,
            file.filename,
            file_type
        )
        
        cloudinary_url = await upload_task
        
        # Perform audit check
        audit_result = perform_audit(groq_response, json_data, db)
        
        # Reject if restricted items found
        if audit_result and audit_result.approval_status == "rejected":
            raise HTTPException(
                status_code=400, 
                detail=f"Document rejected: Restricted items found. Document cannot be approved."
            )
        
        # Only save to database if all validations pass
        max_retries = 3
        for attempt in range(max_retries):
            try:
                new_document = Document(
                    file_hash=file_hash,
                    file_type=file_type,
                    original_filename=file.filename,
                    cloudinary_url=cloudinary_url,
                    groq_response=groq_response,
                    audit_result=audit_result.dict() if audit_result else None
                )
                
                db.add(new_document)
                db.commit()
                db.refresh(new_document)
                break
            except Exception as db_error:
                db.rollback()
                if attempt == max_retries - 1:
                    raise db_error
                await asyncio.sleep(1)
        
        response_data = DocumentResponse(**new_document.__dict__)
        if audit_result:
            response_data.audit_result = audit_result
        
        return UploadResponse(
            success=True,
            message="Document processed and audited successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/documents", response_model=List[DocumentResponse])
async def get_all_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [DocumentResponse(**doc.__dict__) for doc in documents]

@app.get("/document/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(**document.__dict__)

@app.get("/audit-policies", response_model=List[AuditPolicyResponse])
async def get_audit_policies(db: Session = Depends(get_db)):
    policies = db.query(AuditPolicy).all()
    return [AuditPolicyResponse(**policy.__dict__) for policy in policies]

@app.get("/audit-rules")
async def get_audit_rules(db: Session = Depends(get_db)):
    rules = db.query(AuditRule).all()
    return [{"id": rule.id, "category": rule.category, "max_limit": rule.max_limit, "is_restricted": rule.is_restricted, "description": rule.description} for rule in rules]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Document processing API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)