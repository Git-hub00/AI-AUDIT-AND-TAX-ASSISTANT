from pydantic_settings import BaseSettings
import os
import secrets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Database
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "ai_audit_tax_db")
    
    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # AI/LLM API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    class Config:
        env_file = ".env"

settings = Settings()
print(f"Loaded settings - DB: {settings.mongodb_url[:20]}..., JWT Key: {settings.jwt_secret_key[:10]}...")