from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.transactions import router as transactions_router
from app.api.audit import router as audit_router
from app.api.tax import router as tax_router
from app.api.chatbot import router as chatbot_router
from app.api.dashboard import router as dashboard_router

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection

app = FastAPI(
    title="AI Audit & Tax Assistant API",
    description="AI-powered financial document processing and tax assistance",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"Failed to connect to database: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_mongo_connection()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(documents_router, prefix="/api/documents", tags=["documents"])
app.include_router(transactions_router, prefix="/api/transactions", tags=["transactions"])
app.include_router(audit_router, prefix="/api/audit", tags=["audit"])
app.include_router(tax_router, prefix="/api/tax", tags=["tax"])
app.include_router(chatbot_router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    return {"message": "AI Audit & Tax Assistant API", "version": "1.0.0", "status": "running"}

# Dashboard endpoints moved to dashboard router

if __name__ == "__main__":
    import uvicorn
    try:
        print("Starting AI Audit & Tax Assistant API...")
        print(f"Environment: {settings.environment}")
        print(f"Debug mode: {settings.debug}")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
    except Exception as e:
        print(f"Failed to start server: {e}")
        exit(1)