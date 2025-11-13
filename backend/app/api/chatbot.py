from fastapi import APIRouter, HTTPException, Depends
from app.core.security import verify_token
from app.agent.csv_agent import CSVAgent
from typing import List, Optional
from pydantic import BaseModel
from fastapi import UploadFile, File
from fastapi.responses import Response

router = APIRouter()
csv_agent = CSVAgent()

class ChatRequest(BaseModel):
    message: str
    voice: bool = False

@router.post("/message")
async def send_message(
    message_data: dict,
    current_user: dict = Depends(verify_token)
):
    """Send message to AI chatbot"""
    
    try:
        message = message_data.get("message", "").strip()
        
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Use Gemini agent directly
        result = await gemini_agent.process_query(message, {})
        
        return {
            "message": message,
            "response": result["response"],
            "type": result["type"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/conversations")
async def get_conversations(
    limit: int = 20,
    current_user: dict = Depends(verify_token)
):
    """Get conversation history"""
    
    return {
        "conversations": [],
        "total": 0
    }

@router.post("/pin-document")
async def pin_document(
    pin_data: dict,
    current_user: dict = Depends(verify_token)
):
    """Pin document for conversation context"""
    
    return {"success": True, "message": "Document pinned successfully"}

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(verify_token)
):
    """Upload CSV file for processing"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        file_content = await file.read()
        result = csv_agent.process_file_upload(file_content, file.filename)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error uploading file: {str(e)}"
        }

@router.post("/process-command")
async def process_command(
    request: dict,
    current_user: dict = Depends(verify_token)
):
    """Process user command for CSV filtering"""
    try:
        session_id = request.get("session_id")
        command = request.get("command")
        
        if not session_id or not command:
            raise HTTPException(status_code=400, detail="Session ID and command are required")
        
        result = csv_agent.process_command(session_id, command)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing command: {str(e)}"
        }

@router.post("/generate-files")
async def generate_files(
    request: dict,
    current_user: dict = Depends(verify_token)
):
    """Generate CSV files for download"""
    try:
        session_id = request.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID is required")
        
        result = csv_agent.generate_download_files(session_id)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating files: {str(e)}"
        }

@router.get("/download/{session_id}/{filename}")
async def download_file(
    session_id: str,
    filename: str,
    current_user: dict = Depends(verify_token)
):
    """Download generated CSV file"""
    try:
        file_content = csv_agent.get_file_content(session_id, filename)
        
        if not file_content:
            raise HTTPException(status_code=404, detail="File not found")
        
        return Response(
            content=file_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@router.post("/csv-chat")
async def csv_chat(
    request: ChatRequest,
    current_user: dict = Depends(verify_token)
):
    """Chat interface for CSV processing"""
    try:
        message = request.message.lower()
        
        # Check if user is asking about CSV functionality
        if any(word in message for word in ['csv', 'upload', 'file', 'bank statement', 'transactions']):
            return {
                "response": "I can help you process CSV files! Upload a bank statement or transaction file, and I'll help you filter the data.\n\nJust say things like:\n• 'Show only credit transactions'\n• 'List debits above ₹2000'\n• 'Give credits and debits separately'\n\nUpload a CSV file to get started!",
                "type": "csv_help",
                "action": "show_upload"
            }
        
        return {
            "response": "I'm your CSV Processing Assistant! I can help you filter and analyze bank statements and transaction files. Upload a CSV file to begin.",
            "type": "general",
            "action": None
        }
        
    except Exception as e:
        return {
            "response": "I'm here to help you process CSV files. Upload a bank statement to get started!",
            "type": "error",
            "action": None
        }

@router.post("/chat")
async def chat_simple(
    chat_data: dict
):
    """Simple fallback chat endpoint"""
    message = chat_data.get("message", "").strip()
    
    if not message:
        return {"response": "Hello! I'm your AI Tax Auditor Assistant developed by Gowtham from CSBS at KSR Angasamy College of Technology. How can I help you today?"}
    
    return {
        "response": "I'm your AI Tax Auditor Assistant developed by Gowtham from CSBS at KSR Angasamy College of Technology. I can help with tax calculations, audit findings, and financial analysis. Please use the main chat interface for full AI capabilities."
    }