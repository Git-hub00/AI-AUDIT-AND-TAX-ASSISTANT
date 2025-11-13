from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import Optional
from app.models.schemas import DocumentUpload, Document, ParsedData
from app.core.security import verify_token
from app.core.database import get_database
from app.services.document_processor_simple import DocumentProcessor
from bson import ObjectId
import uuid
import os

router = APIRouter()
document_processor = DocumentProcessor()

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    client_id: Optional[str] = Form(None),
    doc_type: str = Form("invoice"),
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Upload a document for processing"""
    
    # Validate file type
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.csv'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not supported"
        )
    
    # Generate unique filename and storage path
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    storage_path = f"documents/{current_user['user_id']}/{unique_filename}"
    
    # TODO: Save file to S3 or local storage
    # For now, we'll simulate storage
    
    # Create document record
    document_data = {
        "user_id": ObjectId(current_user["user_id"]),
        "client_id": ObjectId(client_id) if client_id else None,
        "filename": file.filename,
        "storage_path": storage_path,
        "type": doc_type,
        "status": "uploaded",
        "meta": {
            "size_bytes": file.size,
            "content_type": file.content_type
        }
    }
    
    result = await db.documents.insert_one(document_data)
    
    return {
        "document_id": str(result.inserted_id),
        "status": "uploaded"
    }

@router.post("/{document_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def process_document(
    document_id: str,
    sync: bool = False,
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Process uploaded document for OCR and data extraction"""
    
    # Find document
    document = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "user_id": ObjectId(current_user["user_id"])
    })
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update status to processing
    await db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {"status": "processing"}}
    )
    
    if sync:
        # Process synchronously (for small files)
        try:
            parsed_data = await document_processor.process_document(document)
            
            # Update document with parsed data
            await db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": {
                        "status": "done",
                        "parsed_data": parsed_data,
                        "ocr_confidence": parsed_data.get("confidence", 0.0)
                    }
                }
            )
            
            return {"status": "completed", "parsed_data": parsed_data}
            
        except Exception as e:
            await db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"status": "error", "error_message": str(e)}}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Processing failed: {str(e)}"
            )
    else:
        # TODO: Queue for background processing with Celery
        job_id = str(uuid.uuid4())
        return {"job_id": job_id, "status": "queued"}

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Get document details and parsed data"""
    
    document = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "user_id": ObjectId(current_user["user_id"])
    })
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Convert ObjectId to string for JSON serialization
    document["_id"] = str(document["_id"])
    document["user_id"] = str(document["user_id"])
    if document.get("client_id"):
        document["client_id"] = str(document["client_id"])
    
    return document

@router.patch("/{document_id}/parsed")
async def update_parsed_data(
    document_id: str,
    parsed_data: dict,
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """Update parsed transaction data after manual correction"""
    
    # Verify document ownership
    document = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "user_id": ObjectId(current_user["user_id"])
    })
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update parsed data
    await db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": {"parsed_data": parsed_data}}
    )
    
    # TODO: Save corrected data as training data for ML models
    
    return {"updated": True}

@router.get("/")
async def list_documents(
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(verify_token),
    db = Depends(get_database)
):
    """List user's documents with optional filtering"""
    
    # Build query
    query = {"user_id": ObjectId(current_user["user_id"])}
    if client_id:
        query["client_id"] = ObjectId(client_id)
    if status:
        query["status"] = status
    
    # Get total count
    total = await db.documents.count_documents(query)
    
    # Get documents with pagination
    skip = (page - 1) * limit
    cursor = db.documents.find(query).skip(skip).limit(limit).sort("uploaded_at", -1)
    documents = await cursor.to_list(length=limit)
    
    # Convert ObjectIds to strings
    for doc in documents:
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        if doc.get("client_id"):
            doc["client_id"] = str(doc["client_id"])
    
    return {
        "documents": documents,
        "total": total,
        "page": page,
        "limit": limit
    }