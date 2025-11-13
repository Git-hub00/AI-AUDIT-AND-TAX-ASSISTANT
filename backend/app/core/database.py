from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import asyncio

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    if db.database is None:
        await connect_to_mongo()
    return db.database

async def connect_to_mongo():
    """Create database connection"""
    try:
        print(f"Connecting to MongoDB: {settings.mongodb_url[:30]}...")
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        db.database = db.client[settings.database_name]
        
        # Test connection with timeout
        await asyncio.wait_for(db.client.admin.command('ping'), timeout=10.0)
        print("Connected to MongoDB successfully")
        
        # Create indexes
        await create_indexes()
    except asyncio.TimeoutError:
        print("MongoDB connection timeout")
        raise Exception("Database connection timeout")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    try:
        if db.client:
            db.client.close()
            print("MongoDB connection closed")
    except Exception as e:
        print(f"Error closing MongoDB connection: {e}")

async def create_indexes():
    """Create necessary database indexes"""
    try:
        # Users collection indexes
        await db.database.users.create_index("email", unique=True)
        
        # Documents collection indexes
        await db.database.documents.create_index("user_id")
        await db.database.documents.create_index("status")
        await db.database.documents.create_index([("$**", "text")])  # Text search
        
        # Transactions collection indexes
        await db.database.transactions.create_index([("user_id", 1), ("date", -1)])
        await db.database.transactions.create_index("anomaly_score")
        await db.database.transactions.create_index("document_id")
        
        # Tax records collection indexes
        await db.database.tax_records.create_index([("user_id", 1), ("fiscal_year", -1)])
        
        # Anomaly reports collection indexes
        await db.database.anomaly_reports.create_index([("user_id", 1), ("created_at", -1)])
        
        # Chat messages collection indexes
        await db.database.chat_messages.create_index([("user_id", 1), ("created_at", -1)])
        await db.database.chat_messages.create_index("context_documents")
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")
        # Don't raise here as indexes might already exist