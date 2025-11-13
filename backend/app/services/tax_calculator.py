import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import joblib
import os
from bson import ObjectId
from app.core.database import get_database
from app.models.schemas import TaxRecord, TransactionDB

class TaxCalculator:
    def __init__(self):
        self.model = None
        # Use absolute path for model loading
        import os
        # Get the project root directory (3 levels up from services)
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.model_path = os.path.join(current_dir, "ml_models", "tax_model_v1.joblib")
        self.tax_slabs = self._load_tax_slabs()
        
        # Load pre-trained model if available
        self._load_model()

    def _load_model(self):
        """Load pre-trained tax prediction model"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"Loaded pre-trained tax prediction model from {self.model_path}")
                
                # Load metadata if available
                metadata_path = self.model_path.replace('.joblib', '_metadata.json')
                if os.path.exists(metadata_path):
                    import json
                    with open(metadata_path, 'r') as f:
                        self.model_metadata = json.load(f)
                    print(f"Model metadata: {self.model_metadata.get('model_type', 'Unknown')} trained at {self.model_metadata.get('trained_at', 'Unknown')}")
                else:
                    self.model_metadata = {}
            else:
                print(f"No pre-trained tax model found at {self.model_path}, using rule-based calculation")
                self.model_metadata = {}
        except Exception as e:
            print(f"Error loading tax model: {e}")
            self.model = None
            self.model_metadata = {}

    def _load_tax_slabs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load tax slabs for different fiscal years and jurisdictions"""
        
        # Indian tax slabs for different years (example)
        return {
            "2024": [
                {"min": 0, "max": 250000, "rate": 0.0, "description": "No tax"},
                {"min": 250000, "max": 500000, "rate": 0.05, "description": "5% tax"},
                {"min": 500000, "max": 1000000, "rate": 0.20, "description": "20% tax"},
                {"min": 1000000, "max": float('inf'), "rate": 0.30, "description": "30% tax"}
            ],
            "2023": [
                {"min": 0, "max": 250000, "rate": 0.0, "description": "No tax"},
                {"min": 250000, "max": 500000, "rate": 0.05, "description": "5% tax"},
                {"min": 500000, "max": 1000000, "rate": 0.20, "description": "20% tax"},
                {"min": 1000000, "max": float('inf'), "rate": 0.30, "description": "30% tax"}
            ]
        }

    async def predict_tax(
        self, 
        user_id: str, 
        fiscal_year: str, 
        transactions: List[Dict[str, Any]], 
        deductions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Predict tax liability using ML model and rule-based calculation"""
        
        # Aggregate income from transactions
        income_breakdown = self._aggregate_income(transactions)
        
        # Calculate basic tax using rules
        basic_calculation = self.calculate_basic_tax(
            income=income_breakdown["total_income"],
            deductions=deductions,
            fiscal_year=fiscal_year
        )
        
        # If ML model is available, use it for refinement
        if self.model:
            ml_prediction = await self._predict_with_ml(
                income_breakdown, deductions, fiscal_year
            )
            
            # Combine rule-based and ML predictions
            predicted_tax = (basic_calculation["total_tax"] * 0.7) + (ml_prediction["predicted_tax"] * 0.3)
            confidence = ml_prediction["confidence"]
            explainability = ml_prediction["explainability"]
        else:
            predicted_tax = basic_calculation["total_tax"]
            confidence = 0.85  # High confidence for rule-based calculation
            explainability = self._generate_rule_based_explanation(basic_calculation)
        
        # Analyze individual transactions
        transaction_analysis = self._analyze_transactions(transactions, predicted_tax)
        
        result = {
            "predicted_tax": round(predicted_tax, 2),
            "breakdown": {
                "taxable_income": basic_calculation["taxable_income"],
                "slab_details": basic_calculation["slab_calculations"],
                "credits": basic_calculation.get("credits", 0),
                "total_deductions": sum(deductions.values()) if deductions else 0
            },
            "confidence": confidence,
            "explainability": explainability,
            "income_breakdown": income_breakdown,
            "transaction_analysis": transaction_analysis
        }
        
        # Store tax record in database
        await self._store_tax_record(user_id, fiscal_year, result, deductions)
        
        return result

    def calculate_basic_tax(
        self, 
        income: float, 
        deductions: Dict[str, float], 
        fiscal_year: str
    ) -> Dict[str, Any]:
        """Calculate tax using rule-based slab system"""
        
        # Get tax slabs for the fiscal year
        slabs = self.tax_slabs.get(fiscal_year, self.tax_slabs["2024"])
        
        # Calculate total deductions
        total_deductions = sum(deductions.values()) if deductions else 0
        
        # Calculate taxable income
        taxable_income = max(0, income - total_deductions)
        
        # Calculate tax using slabs
        total_tax = 0
        slab_calculations = []
        remaining_income = taxable_income
        
        for slab in slabs:
            if remaining_income <= 0:
                break
            
            slab_min = slab["min"]
            slab_max = slab["max"]
            rate = slab["rate"]
            
            # Calculate taxable amount in this slab
            if remaining_income > (slab_max - slab_min):
                taxable_in_slab = slab_max - slab_min
            else:
                taxable_in_slab = remaining_income
            
            # Skip if income is below this slab
            if taxable_income <= slab_min:
                continue
            
            # Adjust for income above slab minimum
            if taxable_income > slab_min:
                if taxable_income <= slab_max:
                    taxable_in_slab = taxable_income - slab_min
                else:
                    taxable_in_slab = slab_max - slab_min
            
            tax_in_slab = taxable_in_slab * rate
            total_tax += tax_in_slab
            
            slab_calculations.append({
                "slab_range": f"₹{slab_min:,.0f} - ₹{slab_max:,.0f}" if slab_max != float('inf') else f"₹{slab_min:,.0f}+",
                "rate": f"{rate:.1%}",
                "taxable_amount": taxable_in_slab,
                "tax_amount": tax_in_slab
            })
            
            remaining_income -= taxable_in_slab
        
        return {
            "total_income": income,
            "total_deductions": total_deductions,
            "taxable_income": taxable_income,
            "total_tax": total_tax,
            "slab_calculations": slab_calculations,
            "effective_rate": (total_tax / income * 100) if income > 0 else 0
        }

    def _aggregate_income(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate income from transactions by category"""
        
        income_categories = {
            "salary": 0,
            "business": 0,
            "capital_gains": 0,
            "interest": 0,
            "rental": 0,
            "other": 0
        }
        
        total_income = 0
        
        for txn in transactions:
            amount = abs(txn.get("amount", 0))
            category = txn.get("category", "other").lower()
            
            # Map transaction categories to income categories
            if category in ["salary", "wages", "bonus"]:
                income_categories["salary"] += amount
            elif category in ["business", "consulting", "freelance"]:
                income_categories["business"] += amount
            elif category in ["investment", "stocks", "capital_gains"]:
                income_categories["capital_gains"] += amount
            elif category in ["interest", "dividends"]:
                income_categories["interest"] += amount
            elif category in ["rental", "property"]:
                income_categories["rental"] += amount
            else:
                # Only count positive amounts as income for other categories
                if amount > 0:
                    income_categories["other"] += amount
            
            total_income += amount
        
        return {
            "total_income": total_income,
            "by_category": income_categories,
            "transaction_count": len(transactions)
        }

    async def _predict_with_ml(
        self, 
        income_breakdown: Dict[str, Any], 
        deductions: Dict[str, float], 
        fiscal_year: str
    ) -> Dict[str, Any]:
        """Use ML model to predict tax with explainability"""
        
        # Prepare features for ML model
        features = self._prepare_ml_features(income_breakdown, deductions, fiscal_year)
        
        # Make prediction
        predicted_tax = self.model.predict([features])[0]
        
        # Calculate confidence (simplified)
        confidence = 0.75  # TODO: Implement proper confidence calculation
        
        # Generate explainability (simplified SHAP-like)
        explainability = self._generate_ml_explanation(features, predicted_tax)
        
        return {
            "predicted_tax": predicted_tax,
            "confidence": confidence,
            "explainability": explainability
        }

    def _prepare_ml_features(
        self, 
        income_breakdown: Dict[str, Any], 
        deductions: Dict[str, float], 
        fiscal_year: str
    ) -> List[float]:
        """Prepare features for ML model matching training format"""
        
        total_income = income_breakdown["total_income"]
        salary_income = income_breakdown["by_category"]["salary"]
        business_income = income_breakdown["by_category"]["business"]
        capital_gains = income_breakdown["by_category"]["capital_gains"]
        total_deductions = sum(deductions.values()) if deductions else 0
        taxable_income = max(0, total_income - total_deductions)
        
        # Calculate derived features to match training data
        income_diversity = len([x for x in [salary_income, business_income, capital_gains] if x > 0])
        deduction_ratio = total_deductions / total_income if total_income > 0 else 0
        log_total_income = np.log1p(total_income)
        log_taxable_income = np.log1p(taxable_income)
        
        features = [
            total_income,
            salary_income,
            business_income,
            capital_gains,
            total_deductions,
            taxable_income,
            int(fiscal_year),
            income_diversity,
            deduction_ratio,
            log_total_income,
            log_taxable_income
        ]
        
        return features

    def _generate_ml_explanation(self, features: List[float], predicted_tax: float) -> Dict[str, List[Dict[str, float]]]:
        """Generate ML model explanation (simplified SHAP-like)"""
        
        feature_names = [
            "total_income", "salary_income", "business_income", 
            "capital_gains", "interest_income", "total_deductions",
            "fiscal_year", "transaction_count"
        ]
        
        # Simplified feature importance (in real implementation, use SHAP)
        base_importance = [0.4, 0.3, 0.15, 0.05, 0.03, 0.25, 0.01, 0.01]
        
        explanations = []
        for i, (name, importance) in enumerate(zip(feature_names, base_importance)):
            impact = features[i] * importance * (predicted_tax / 100000)  # Normalize
            explanations.append({
                "feature": name,
                "impact": round(impact, 2),
                "value": features[i]
            })
        
        # Sort by absolute impact
        explanations.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return {"top_features": explanations[:5]}

    def _generate_rule_based_explanation(self, calculation: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate explanation for rule-based calculation"""
        
        explanations = [
            {
                "feature": "taxable_income",
                "impact": calculation["total_tax"],
                "description": f"Tax calculated on ₹{calculation['taxable_income']:,.0f} taxable income"
            },
            {
                "feature": "tax_slabs",
                "impact": calculation["total_tax"],
                "description": f"Applied progressive tax slabs with {calculation['effective_rate']:.1f}% effective rate"
            }
        ]
        
        if calculation["total_deductions"] > 0:
            explanations.append({
                "feature": "deductions",
                "impact": -calculation["total_deductions"] * 0.2,  # Approximate tax saved
                "description": f"₹{calculation['total_deductions']:,.0f} in deductions reduced tax liability"
            })
        
        return {"top_features": explanations}

    def _analyze_transactions(self, transactions: List[Dict[str, Any]], total_tax: float) -> Dict[str, Any]:
        """Analyze individual transactions for tax implications"""
        
        analyzed_transactions = []
        receipt_required = []
        
        for i, txn in enumerate(transactions):
            amount = abs(txn.get("amount", 0))
            category = txn.get("category", "other").lower()
            
            # Calculate tax impact for this transaction
            tax_rate = self._get_applicable_tax_rate(amount, category)
            tax_impact = amount * tax_rate
            
            # Determine if receipt is required
            needs_receipt = self._requires_receipt(amount, category)
            
            # Classify transaction type
            txn_type = self._classify_transaction_type(category, amount)
            
            analysis = {
                "transaction_id": i + 1,
                "amount": amount,
                "category": category,
                "type": txn_type,
                "tax_impact": round(tax_impact, 2),
                "tax_rate": f"{tax_rate:.1%}",
                "deductible": self._is_deductible(category),
                "receipt_required": needs_receipt,
                "compliance_notes": self._get_compliance_notes(category, amount),
                "tax_calculation": {
                    "base_amount": amount,
                    "applicable_rate": tax_rate,
                    "calculated_tax": tax_impact,
                    "effective_rate": (tax_impact / amount * 100) if amount > 0 else 0
                }
            }
            
            analyzed_transactions.append(analysis)
            
            if needs_receipt:
                receipt_required.append({
                    "transaction_id": i + 1,
                    "amount": amount,
                    "category": category,
                    "reason": self._get_receipt_reason(category, amount)
                })
        
        return {
            "transactions": analyzed_transactions,
            "receipt_requirements": receipt_required,
            "summary": {
                "total_transactions": len(transactions),
                "receipt_required_count": len(receipt_required),
                "total_tax_impact": sum(t["tax_impact"] for t in analyzed_transactions),
                "deductible_transactions": len([t for t in analyzed_transactions if t["deductible"]]),
                "average_tax_rate": (sum(t["tax_impact"] for t in analyzed_transactions) / sum(t["amount"] for t in analyzed_transactions) * 100) if analyzed_transactions else 0
            }
        }

    def _get_applicable_tax_rate(self, amount: float, category: str) -> float:
        """Get applicable tax rate for transaction"""
        if category in ["salary", "wages"]:
            return 0.20 if amount > 500000 else 0.05
        elif category in ["business", "consulting"]:
            return 0.30 if amount > 1000000 else 0.20
        elif category in ["capital_gains", "investment"]:
            return 0.15
        else:
            return 0.10

    def _requires_receipt(self, amount: float, category: str) -> bool:
        """Determine if receipt is required for tax filing"""
        # High-value transactions always need receipts
        if amount > 50000:
            return True
        
        # Business expenses need receipts
        if category in ["business", "consulting", "professional"]:
            return amount > 5000
        
        # Investment and deductible items need receipts
        if category in ["investment", "insurance", "medical", "education"]:
            return amount > 10000
        
        return False

    def _classify_transaction_type(self, category: str, amount: float) -> str:
        """Classify transaction for tax purposes"""
        if category in ["salary", "wages", "bonus"]:
            return "Employment Income"
        elif category in ["business", "consulting", "freelance"]:
            return "Business Income"
        elif category in ["investment", "dividends", "capital_gains"]:
            return "Investment Income"
        elif category in ["rental", "property"]:
            return "Rental Income"
        else:
            return "Other Income"

    def _is_deductible(self, category: str) -> bool:
        """Check if transaction is tax deductible"""
        deductible_categories = [
            "insurance", "medical", "education", "charity", 
            "home_loan", "investment", "professional"
        ]
        return category.lower() in deductible_categories

    def _get_compliance_notes(self, category: str, amount: float) -> List[str]:
        """Get compliance notes for transaction"""
        notes = []
        
        if amount > 200000:
            notes.append("High-value transaction - ensure proper documentation")
        
        if category in ["cash", "cash_deposit"] and amount > 50000:
            notes.append("Cash transaction above ₹50,000 - may require PAN disclosure")
        
        if category in ["business", "consulting"] and amount > 30000:
            notes.append("TDS may be applicable - verify deduction")
        
        if category in ["investment", "mutual_fund"] and amount > 100000:
            notes.append("Capital gains tax implications - maintain purchase records")
        
        return notes

    def _get_receipt_reason(self, category: str, amount: float) -> str:
        """Get reason why receipt is required"""
        if amount > 50000:
            return "High-value transaction requires documentation"
        elif category in ["business", "professional"]:
            return "Business expense deduction requires receipt"
        elif category in ["medical", "insurance"]:
            return "Tax deduction under 80D requires receipt"
        elif category in ["investment"]:
            return "Investment proof required for 80C deduction"
        else:
            return "Documentation required for tax compliance"

    def get_tax_slabs(self, fiscal_year: str) -> List[Dict[str, Any]]:
        """Get tax slabs for a specific fiscal year"""
        return self.tax_slabs.get(fiscal_year, self.tax_slabs["2024"])

    def calculate_tax_savings(
        self, 
        current_deductions: Dict[str, float], 
        additional_deductions: Dict[str, float], 
        income: float, 
        fiscal_year: str
    ) -> Dict[str, Any]:
        """Calculate potential tax savings from additional deductions"""
        
        # Calculate current tax
        current_tax = self.calculate_basic_tax(income, current_deductions, fiscal_year)
        
        # Calculate tax with additional deductions
        all_deductions = {**current_deductions, **additional_deductions}
        new_tax = self.calculate_basic_tax(income, all_deductions, fiscal_year)
        
        savings = current_tax["total_tax"] - new_tax["total_tax"]
        
        return {
            "current_tax": current_tax["total_tax"],
            "new_tax": new_tax["total_tax"],
            "tax_savings": savings,
            "additional_deductions": sum(additional_deductions.values()),
            "savings_percentage": (savings / current_tax["total_tax"] * 100) if current_tax["total_tax"] > 0 else 0
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_loaded": self.model is not None,
            "model_path": self.model_path,
            "model_exists": os.path.exists(self.model_path),
            "metadata": getattr(self, 'model_metadata', {}),
            "prediction_method": "ML Model" if self.model else "Rule-based"
        }

    def save_model(self, model, model_path: str = None):
        """Save trained tax prediction model"""
        
        model_path = model_path or self.model_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save model
        joblib.dump(model, model_path)
        
        # Save metadata
        metadata = {
            "model_type": "tax_prediction",
            "trained_at": datetime.utcnow().isoformat(),
            "features": [
                "total_income", "salary_income", "business_income", 
                "capital_gains", "interest_income", "total_deductions",
                "fiscal_year", "transaction_count"
            ]
        }
        
        metadata_path = model_path.replace('.joblib', '_metadata.json')
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Saved tax prediction model to {model_path}")

    def generate_tax_report(self, prediction_result: Dict[str, Any], user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive tax report"""
        
        from datetime import datetime
        
        # Handle different data formats from frontend
        if "income_breakdown" in prediction_result:
            # Backend format
            total_income = prediction_result["income_breakdown"]["total_income"]
            taxable_income = prediction_result["breakdown"]["taxable_income"]
        else:
            # Frontend format
            total_income = prediction_result.get("totalIncome", 0)
            taxable_income = prediction_result.get("taxableIncome", 0)
        
        predicted_tax = prediction_result.get("predicted_tax", prediction_result.get("predictedTax", 0))
        effective_rate = (predicted_tax / total_income * 100) if total_income > 0 else 0
        
        report = {
            "report_id": f"TAX-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "user_info": user_info,
            "tax_summary": {
                "total_income": total_income,
                "taxable_income": taxable_income,
                "predicted_tax": predicted_tax,
                "effective_rate": effective_rate
            },
            "transaction_analysis": prediction_result.get("transaction_analysis", {}),
            "recommendations": prediction_result.get("recommendations", []),
            "compliance_checklist": self._generate_compliance_checklist(prediction_result)
        }
        
        return report

    def _generate_tax_recommendations(self, prediction_result: Dict[str, Any]) -> List[str]:
        """Generate tax optimization recommendations"""
        recommendations = []
        
        # Handle different data formats
        if "income_breakdown" in prediction_result:
            total_income = prediction_result["income_breakdown"]["total_income"]
            deductions = prediction_result["breakdown"]["total_deductions"]
        else:
            total_income = prediction_result.get("totalIncome", 0)
            deductions = prediction_result.get("deductions", 0)
        
        if deductions < 150000:
            recommendations.append("Maximize 80C deductions up to ₹1.5L (PPF, ELSS, NSC)")
        
        if total_income > 500000 and deductions < 50000:
            recommendations.append("Consider health insurance for 80D deductions up to ₹25,000")
        
        receipt_count = len(prediction_result.get("transaction_analysis", {}).get("receipt_requirements", []))
        if receipt_count > 0:
            recommendations.append(f"Collect {receipt_count} missing receipts for tax filing")
        
        return recommendations

    def _generate_compliance_checklist(self, prediction_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate compliance checklist"""
        checklist = [
            {"item": "Form 16 from employer", "required": True, "status": "pending"},
            {"item": "Investment proofs (80C)", "required": True, "status": "pending"},
            {"item": "Bank statements", "required": True, "status": "pending"},
            {"item": "Interest certificates", "required": False, "status": "optional"}
        ]
        
        # Add receipt requirements safely
        try:
            receipt_reqs = prediction_result.get("transaction_analysis", {}).get("receipt_requirements", [])
            for req in receipt_reqs:
                checklist.append({
                    "item": f"Receipt for {req.get('category', 'transaction')} - Rs.{req.get('amount', 0):,.0f}",
                    "required": True,
                    "status": "pending",
                    "reason": req.get("reason", "Documentation required")
                })
        except Exception as e:
            print(f"Error generating compliance checklist: {e}")
        
        return checklist

    async def _store_tax_record(
        self, 
        user_id: str, 
        fiscal_year: str, 
        prediction_result: Dict[str, Any], 
        deductions: Dict[str, float]
    ):
        """Store tax record in database"""
        try:
            db = await get_database()
            
            tax_record = TaxRecord(
                user_id=ObjectId(user_id),
                fiscal_year=fiscal_year,
                total_income=prediction_result["income_breakdown"]["total_income"],
                total_deductions=sum(deductions.values()) if deductions else 0,
                taxable_income=prediction_result["breakdown"]["taxable_income"],
                predicted_tax=prediction_result["predicted_tax"],
                confidence_score=prediction_result["confidence"],
                income_breakdown=prediction_result["income_breakdown"]["by_category"],
                deduction_breakdown=deductions or {},
                transactions_analyzed=prediction_result["income_breakdown"]["transaction_count"],
                model_version="v1"
            )
            
            await db.tax_records.insert_one(tax_record.dict(by_alias=True))
            print(f"Stored tax record for user {user_id}, fiscal year {fiscal_year}")
            
        except Exception as e:
            print(f"Error storing tax record: {e}")

    async def store_transactions(
        self, 
        user_id: str, 
        document_id: str, 
        transactions: List[Dict[str, Any]]
    ):
        """Store transactions in database"""
        try:
            db = await get_database()
            
            transaction_docs = []
            for txn in transactions:
                transaction_doc = TransactionDB(
                    document_id=ObjectId(document_id),
                    user_id=ObjectId(user_id),
                    date=datetime.fromisoformat(txn["date"]) if isinstance(txn["date"], str) else txn["date"],
                    amount=float(txn["amount"]),
                    currency=txn.get("currency", "INR"),
                    description=txn["description"],
                    merchant=txn["merchant"],
                    category=txn["category"]
                )
                transaction_docs.append(transaction_doc.dict(by_alias=True))
            
            if transaction_docs:
                await db.transactions.insert_many(transaction_docs)
                print(f"Stored {len(transaction_docs)} transactions for user {user_id}")
                
        except Exception as e:
            print(f"Error storing transactions: {e}")

    async def get_tax_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get tax calculation history for user"""
        try:
            db = await get_database()
            
            cursor = db.tax_records.find(
                {"user_id": ObjectId(user_id)}
            ).sort("created_at", -1).limit(limit)
            
            records = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for record in records:
                record["_id"] = str(record["_id"])
                record["user_id"] = str(record["user_id"])
            
            return records
            
        except Exception as e:
            print(f"Error getting tax history: {e}")
            return []

    async def get_user_transactions(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user transactions for AI chatbot context"""
        try:
            db = await get_database()
            
            cursor = db.transactions.find(
                {"user_id": ObjectId(user_id)}
            ).sort("date", -1).limit(limit)
            
            transactions = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for txn in transactions:
                txn["_id"] = str(txn["_id"])
                txn["user_id"] = str(txn["user_id"])
                txn["document_id"] = str(txn["document_id"])
            
            return transactions
            
        except Exception as e:
            print(f"Error getting user transactions: {e}")
            return []

# TODO: Advanced tax calculation features to implement:
# 1. Multi-jurisdiction tax calculation (state, federal, international)
# 2. Tax optimization recommendations
# 3. Quarterly tax estimation
# 4. Tax form generation (1040, etc.)
# 5. Integration with tax filing APIs
# 6. Historical tax comparison and trends
# 7. Tax planning scenarios and what-if analysis
# 8. Transaction-level tax analysis and receipt tracking
# 9. Automated compliance checklist generation
# 10. Export functionality for tax reports