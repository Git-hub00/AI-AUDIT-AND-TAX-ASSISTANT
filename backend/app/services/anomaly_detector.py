import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from bson import ObjectId
from app.core.database import get_database
from app.models.schemas import AnomalyReport, TransactionDB
import joblib
import os

class AnomalyDetector:
    def __init__(self):
        self.model = None
        # Use absolute path for model loading
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.model_path = os.path.join(current_dir, "ml_models", "anomaly_model_v1.joblib")
        self._load_model()

    def _load_model(self):
        """Load pre-trained anomaly detection model"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"Loaded pre-trained anomaly detection model from {self.model_path}")
            else:
                print(f"No pre-trained anomaly model found at {self.model_path}, using rule-based detection")
        except Exception as e:
            print(f"Error loading anomaly model: {e}")
            self.model = None

    async def detect_anomalies(
        self, 
        user_id: str, 
        transactions: List[Dict[str, Any]], 
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """Detect anomalies in transactions and store report"""
        
        # Analyze transactions for anomalies
        anomaly_results = []
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        total_flagged_amount = 0
        
        for i, txn in enumerate(transactions):
            anomaly_score, reasons = self._calculate_anomaly_score(txn, transactions)
            
            risk_level = self._get_risk_level(anomaly_score)
            if risk_level == "High":
                high_risk_count += 1
            elif risk_level == "Medium":
                medium_risk_count += 1
            elif risk_level == "Low":
                low_risk_count += 1
            
            if anomaly_score > 0.3:  # Threshold for flagged transactions
                total_flagged_amount += abs(txn.get("amount", 0))
            
            anomaly_results.append({
                "transaction_id": i + 1,
                "amount": txn.get("amount", 0),
                "merchant": txn.get("merchant", ""),
                "category": txn.get("category", ""),
                "date": txn.get("date", ""),
                "anomaly_score": round(anomaly_score, 3),
                "risk_level": risk_level,
                "reasons": reasons,
                "flagged": anomaly_score > 0.3
            })
        
        anomalous_transactions = len([r for r in anomaly_results if r["flagged"]])
        anomaly_rate = (anomalous_transactions / len(transactions) * 100) if transactions else 0
        
        result = {
            "total_transactions": len(transactions),
            "anomalous_transactions": anomalous_transactions,
            "anomaly_rate": round(anomaly_rate, 2),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "total_flagged_amount": round(total_flagged_amount, 2),
            "anomaly_details": anomaly_results
        }
        
        # Store anomaly report in database
        await self._store_anomaly_report(user_id, document_ids, result)
        
        return result

    def _calculate_anomaly_score(self, transaction: Dict[str, Any], all_transactions: List[Dict[str, Any]]) -> tuple:
        """Calculate anomaly score for a transaction"""
        
        if self.model:
            return self._ml_anomaly_score(transaction, all_transactions)
        else:
            return self._rule_based_anomaly_score(transaction, all_transactions)

    def _rule_based_anomaly_score(self, transaction: Dict[str, Any], all_transactions: List[Dict[str, Any]]) -> tuple:
        """Rule-based anomaly detection"""
        
        amount = abs(transaction.get("amount", 0))
        merchant = transaction.get("merchant", "").lower()
        category = transaction.get("category", "").lower()
        
        score = 0.0
        reasons = []
        
        # Amount-based anomalies
        amounts = [abs(t.get("amount", 0)) for t in all_transactions]
        if amounts:
            mean_amount = np.mean(amounts)
            std_amount = np.std(amounts)
            
            if amount > mean_amount + 2 * std_amount:
                score += 0.4
                reasons.append("Unusually high transaction amount")
            elif amount > mean_amount + std_amount:
                score += 0.2
                reasons.append("Above average transaction amount")
        
        # Frequency-based anomalies
        merchant_counts = {}
        for t in all_transactions:
            m = t.get("merchant", "").lower()
            merchant_counts[m] = merchant_counts.get(m, 0) + 1
        
        if merchant_counts.get(merchant, 0) == 1 and amount > 10000:
            score += 0.3
            reasons.append("First-time high-value merchant")
        
        # Category-based anomalies
        if category in ["cash", "atm", "withdrawal"] and amount > 50000:
            score += 0.5
            reasons.append("Large cash withdrawal")
        
        if category in ["gambling", "casino", "betting"]:
            score += 0.6
            reasons.append("High-risk category transaction")
        
        # Time-based anomalies (simplified)
        if "weekend" in transaction.get("date", "").lower():
            score += 0.1
            reasons.append("Weekend transaction")
        
        # Round amounts (potential fraud indicator)
        if amount % 1000 == 0 and amount > 5000:
            score += 0.2
            reasons.append("Round amount transaction")
        
        return min(score, 1.0), reasons

    def _ml_anomaly_score(self, transaction: Dict[str, Any], all_transactions: List[Dict[str, Any]]) -> tuple:
        """ML-based anomaly detection"""
        
        # Prepare features for ML model
        features = self._prepare_anomaly_features(transaction, all_transactions)
        
        # Get anomaly score from model
        score = self.model.decision_function([features])[0]
        
        # Normalize score to 0-1 range
        normalized_score = max(0, min(1, (score + 0.5) / 1.0))
        
        # Generate explanations
        reasons = self._generate_ml_explanations(features, normalized_score)
        
        return normalized_score, reasons

    def _prepare_anomaly_features(self, transaction: Dict[str, Any], all_transactions: List[Dict[str, Any]]) -> List[float]:
        """Prepare features for ML anomaly detection"""
        
        amount = abs(transaction.get("amount", 0))
        
        # Statistical features
        amounts = [abs(t.get("amount", 0)) for t in all_transactions]
        mean_amount = np.mean(amounts) if amounts else 0
        std_amount = np.std(amounts) if amounts else 0
        
        # Merchant frequency
        merchant = transaction.get("merchant", "").lower()
        merchant_freq = sum(1 for t in all_transactions if t.get("merchant", "").lower() == merchant)
        
        # Category encoding (simplified)
        category = transaction.get("category", "").lower()
        high_risk_categories = ["cash", "gambling", "casino", "atm"]
        category_risk = 1 if category in high_risk_categories else 0
        
        features = [
            amount,
            amount / mean_amount if mean_amount > 0 else 0,
            (amount - mean_amount) / std_amount if std_amount > 0 else 0,
            merchant_freq,
            category_risk,
            1 if amount % 1000 == 0 else 0,  # Round amount
            len(merchant),  # Merchant name length
            1 if amount > 50000 else 0  # High value flag
        ]
        
        return features

    def _generate_ml_explanations(self, features: List[float], score: float) -> List[str]:
        """Generate explanations for ML anomaly score"""
        
        reasons = []
        
        if features[1] > 2:  # Amount ratio
            reasons.append("Transaction amount significantly above average")
        
        if features[3] == 1:  # Merchant frequency
            reasons.append("First transaction with this merchant")
        
        if features[4] == 1:  # Category risk
            reasons.append("High-risk transaction category")
        
        if features[5] == 1:  # Round amount
            reasons.append("Round amount transaction")
        
        if features[7] == 1:  # High value
            reasons.append("High-value transaction")
        
        if score > 0.7:
            reasons.append("Multiple anomaly indicators detected")
        
        return reasons

    def _get_risk_level(self, anomaly_score: float) -> str:
        """Convert anomaly score to risk level"""
        if anomaly_score >= 0.7:
            return "High"
        elif anomaly_score >= 0.4:
            return "Medium"
        elif anomaly_score >= 0.2:
            return "Low"
        else:
            return "Normal"

    async def _store_anomaly_report(
        self, 
        user_id: str, 
        document_ids: List[str], 
        result: Dict[str, Any]
    ):
        """Store anomaly report in database"""
        try:
            db = await get_database()
            
            anomaly_report = AnomalyReport(
                user_id=ObjectId(user_id),
                document_ids=[ObjectId(doc_id) for doc_id in document_ids],
                total_transactions=result["total_transactions"],
                anomalous_transactions=result["anomalous_transactions"],
                anomaly_rate=result["anomaly_rate"],
                high_risk_count=result["high_risk_count"],
                medium_risk_count=result["medium_risk_count"],
                low_risk_count=result["low_risk_count"],
                total_flagged_amount=result["total_flagged_amount"],
                model_version="v1"
            )
            
            await db.anomaly_reports.insert_one(anomaly_report.dict(by_alias=True))
            print(f"Stored anomaly report for user {user_id}")
            
        except Exception as e:
            print(f"Error storing anomaly report: {e}")

    async def update_transaction_anomalies(
        self, 
        user_id: str, 
        document_id: str, 
        anomaly_results: List[Dict[str, Any]]
    ):
        """Update transactions with anomaly scores"""
        try:
            db = await get_database()
            
            for i, result in enumerate(anomaly_results):
                await db.transactions.update_one(
                    {
                        "user_id": ObjectId(user_id),
                        "document_id": ObjectId(document_id)
                    },
                    {
                        "$set": {
                            "anomaly_score": result["anomaly_score"],
                            "anomaly_reasons": [{"reason": r} for r in result["reasons"]]
                        }
                    }
                )
            
            print(f"Updated {len(anomaly_results)} transactions with anomaly scores")
            
        except Exception as e:
            print(f"Error updating transaction anomalies: {e}")

    async def get_anomaly_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get anomaly detection history for user"""
        try:
            db = await get_database()
            
            cursor = db.anomaly_reports.find(
                {"user_id": ObjectId(user_id)}
            ).sort("created_at", -1).limit(limit)
            
            reports = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for report in reports:
                report["_id"] = str(report["_id"])
                report["user_id"] = str(report["user_id"])
                report["document_ids"] = [str(doc_id) for doc_id in report["document_ids"]]
            
            return reports
            
        except Exception as e:
            print(f"Error getting anomaly history: {e}")
            return []

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_loaded": self.model is not None,
            "model_path": self.model_path,
            "model_exists": os.path.exists(self.model_path),
            "detection_method": "ML Model" if self.model else "Rule-based"
        }