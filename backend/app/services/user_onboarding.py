from datetime import datetime, timedelta
from bson import ObjectId
from app.core.database import get_database
import random

class UserOnboardingService:
    def __init__(self):
        pass

    async def create_sample_data_for_user(self, user_id: str):
        """Create sample data for new user to populate dashboard"""
        
        try:
            db = await get_database()
            user_obj_id = ObjectId(user_id)
            
            # Check if user already has data
            existing_docs = await db.documents.count_documents({"user_id": user_obj_id})
            if existing_docs > 0:
                return  # User already has data
            
            # Create sample documents
            sample_documents = []
            for i in range(3):
                doc_id = ObjectId()
                sample_documents.append({
                    "_id": doc_id,
                    "user_id": user_obj_id,
                    "filename": f"sample_document_{i+1}.pdf",
                    "storage_path": f"/uploads/sample_{i+1}.pdf",
                    "type": "invoice",
                    "status": "done",
                    "uploaded_at": datetime.utcnow() - timedelta(days=i)
                })
            
            await db.documents.insert_many(sample_documents)
            
            # Create sample transactions
            sample_transactions = [
                {
                    "id": "1",
                    "date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "amount": 45000,
                    "currency": "INR",
                    "description": "Monthly Salary",
                    "merchant": "Your Company",
                    "category": "salary"
                },
                {
                    "id": "2",
                    "date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                    "amount": 20000,
                    "currency": "INR",
                    "description": "Freelance Work",
                    "merchant": "Client Corp",
                    "category": "business"
                },
                {
                    "id": "3",
                    "date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                    "amount": 15000,
                    "currency": "INR",
                    "description": "Investment",
                    "merchant": "Mutual Fund",
                    "category": "investment"
                }
            ]
            
            # Store transactions directly in database
            from app.models.schemas import TransactionDB
            transaction_docs = []
            for txn in sample_transactions:
                transaction_doc = TransactionDB(
                    document_id=sample_documents[0]["_id"],
                    user_id=user_obj_id,
                    date=datetime.fromisoformat(txn["date"]),
                    amount=float(txn["amount"]),
                    currency=txn["currency"],
                    description=txn["description"],
                    merchant=txn["merchant"],
                    category=txn["category"]
                )
                transaction_docs.append(transaction_doc.dict(by_alias=True))
            
            await db.transactions.insert_many(transaction_docs)
            
            # Create sample tax record
            from app.models.schemas import TaxRecord
            tax_record = TaxRecord(
                user_id=user_obj_id,
                fiscal_year="2024",
                total_income=80000,
                total_deductions=45000,
                taxable_income=35000,
                predicted_tax=1750,
                confidence_score=0.85,
                income_breakdown={"salary": 45000, "business": 20000, "investment": 15000},
                deduction_breakdown={"80c": 30000, "80d": 15000},
                transactions_analyzed=3,
                model_version="v1"
            )
            
            await db.tax_records.insert_one(tax_record.dict(by_alias=True))
            
            # Create sample anomaly report
            from app.models.schemas import AnomalyReport
            anomaly_report = AnomalyReport(
                user_id=user_obj_id,
                document_ids=[doc["_id"] for doc in sample_documents],
                total_transactions=3,
                anomalous_transactions=1,
                anomaly_rate=33.3,
                high_risk_count=1,
                medium_risk_count=0,
                low_risk_count=0,
                total_flagged_amount=20000,
                model_version="v1"
            )
            
            await db.anomaly_reports.insert_one(anomaly_report.dict(by_alias=True))
            
            print(f"Created sample data for user {user_id}")
            
        except Exception as e:
            print(f"Error creating sample data: {e}")

user_onboarding = UserOnboardingService()