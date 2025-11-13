from pydantic import BaseModel, EmailStr, Field
import pydantic
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, values=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

# Add schema helpers depending on pydantic major version to support v1 and v2


def _pydantic_major_version():
    try:
        ver = getattr(pydantic, '__version__', None) or getattr(pydantic, 'VERSION', None)
        if ver:
            return int(str(ver).split('.')[0])
    except Exception:
        pass
    return 1


if _pydantic_major_version() >= 2:
    # pydantic v2: provide json schema hook
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string"}

    PyObjectId.__get_pydantic_json_schema__ = classmethod(__get_pydantic_json_schema__)
else:
    # pydantic v1: use legacy __modify_schema__
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

    PyObjectId.__modify_schema__ = classmethod(__modify_schema__)

# Enums

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

class DocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    STATEMENT = "statement"
    BANK = "bank"

# Auth Schemas
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    email: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Document Schemas
class DocumentUpload(BaseModel):
    type: DocumentType

class Transaction(BaseModel):
    id: str
    date: str
    description: str
    merchant: str
    category: str
    amount: float
    currency: str = "INR"
    source_coords: Optional[Dict[str, Any]] = None

class ParsedData(BaseModel):
    transactions: List[Transaction] = []
    raw_text: str = ""
    tables: List[Dict[str, Any]] = []

class Document(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    filename: str
    storage_path: str
    type: DocumentType
    status: DocumentStatus = DocumentStatus.UPLOADED
    parsed_data: Optional[ParsedData] = None
    ocr_confidence: Optional[float] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    meta: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Transaction Schemas
class TransactionDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    document_id: PyObjectId
    user_id: PyObjectId
    date: datetime
    amount: float
    currency: str = "INR"
    description: str
    merchant: str
    category: str
    anomaly_score: Optional[float] = None
    anomaly_reasons: List[Dict[str, str]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Tax Record Schemas
class TaxRecord(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    fiscal_year: str
    total_income: float
    total_deductions: float
    taxable_income: float
    predicted_tax: float
    confidence_score: float
    income_breakdown: Dict[str, float]
    deduction_breakdown: Dict[str, float]
    transactions_analyzed: int
    model_version: str = "v1"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()

# Anomaly Report Schemas
class AnomalyReport(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    document_ids: List[PyObjectId]
    total_transactions: int
    anomalous_transactions: int
    anomaly_rate: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_flagged_amount: float
    model_version: str = "v1"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        protected_namespaces = ()

# Chat History Schemas
class ChatMessage(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    message: str
    response: str
    context_documents: List[PyObjectId] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}







