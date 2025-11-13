from typing import Dict, List, Any, Optional
from datetime import datetime
from bson import ObjectId
from app.core.database import get_database
from app.models.schemas import ChatMessage

class ChatbotService:
    def __init__(self):
        self.context_limit = 10  # Number of recent messages to keep in context
        
    async def process_message(
        self, 
        user_id: str, 
        message: str, 
        context_documents: List[str] = None
    ) -> Dict[str, Any]:
        """Process user message and generate AI response"""
        
        # Get user context (transactions, tax records, anomaly reports)
        user_context = await self._get_user_context(user_id)
        
        # Get document context if specified
        document_context = []
        if context_documents:
            document_context = await self._get_document_context(user_id, context_documents)
        
        # Get conversation history
        conversation_history = await self._get_conversation_history(user_id)
        
        # Generate AI response based on context
        response = await self._generate_response(
            message=message,
            user_context=user_context,
            document_context=document_context,
            conversation_history=conversation_history
        )
        
        # Store conversation in database
        await self._store_conversation(
            user_id=user_id,
            message=message,
            response=response,
            context_documents=context_documents or []
        )
        
        return {
            "message": message,
            "response": response,
            "context_used": {
                "transactions_count": len(user_context.get("transactions", [])),
                "tax_records_count": len(user_context.get("tax_records", [])),
                "anomaly_reports_count": len(user_context.get("anomaly_reports", [])),
                "documents_count": len(document_context)
            }
        }
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user's financial data context"""
        
        db = await get_database()
        user_obj_id = ObjectId(user_id)
        
        # Get recent transactions
        transactions = await db.transactions.find(
            {"user_id": user_obj_id}
        ).sort("date", -1).limit(50).to_list(50)
        
        # Get tax records
        tax_records = await db.tax_records.find(
            {"user_id": user_obj_id}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        # Get anomaly reports
        anomaly_reports = await db.anomaly_reports.find(
            {"user_id": user_obj_id}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        # Convert ObjectIds to strings
        for txn in transactions:
            txn["_id"] = str(txn["_id"])
            txn["user_id"] = str(txn["user_id"])
            txn["document_id"] = str(txn["document_id"])
        
        for tax in tax_records:
            tax["_id"] = str(tax["_id"])
            tax["user_id"] = str(tax["user_id"])
        
        for anomaly in anomaly_reports:
            anomaly["_id"] = str(anomaly["_id"])
            anomaly["user_id"] = str(anomaly["user_id"])
            anomaly["document_ids"] = [str(doc_id) for doc_id in anomaly["document_ids"]]
        
        return {
            "transactions": transactions,
            "tax_records": tax_records,
            "anomaly_reports": anomaly_reports
        }
    
    async def _get_document_context(self, user_id: str, document_ids: List[str]) -> List[Dict[str, Any]]:
        """Get specific document context"""
        
        db = await get_database()
        user_obj_id = ObjectId(user_id)
        
        documents = []
        for doc_id in document_ids:
            try:
                doc = await db.documents.find_one({
                    "_id": ObjectId(doc_id),
                    "user_id": user_obj_id
                })
                if doc:
                    doc["_id"] = str(doc["_id"])
                    doc["user_id"] = str(doc["user_id"])
                    documents.append(doc)
            except Exception as e:
                print(f"Error getting document {doc_id}: {e}")
        
        return documents
    
    async def _get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        
        db = await get_database()
        user_obj_id = ObjectId(user_id)
        
        messages = await db.chat_messages.find(
            {"user_id": user_obj_id}
        ).sort("created_at", -1).limit(self.context_limit).to_list(self.context_limit)
        
        # Convert ObjectIds and reverse order (oldest first)
        for msg in messages:
            msg["_id"] = str(msg["_id"])
            msg["user_id"] = str(msg["user_id"])
            msg["context_documents"] = [str(doc_id) for doc_id in msg["context_documents"]]
        
        return list(reversed(messages))
    
    async def _generate_response(
        self,
        message: str,
        user_context: Dict[str, Any],
        document_context: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Generate AI response based on context"""
        
        # For now, implement rule-based responses
        # In production, this would use OpenAI API or similar
        
        message_lower = message.lower()
        
        # Tax-related queries
        if any(keyword in message_lower for keyword in ["tax", "income", "deduction", "liability"]):
            return self._generate_tax_response(message_lower, user_context)
        
        # Transaction-related queries
        elif any(keyword in message_lower for keyword in ["transaction", "spending", "expense", "payment"]):
            return self._generate_transaction_response(message_lower, user_context)
        
        # Anomaly-related queries
        elif any(keyword in message_lower for keyword in ["anomaly", "fraud", "suspicious", "risk"]):
            return self._generate_anomaly_response(message_lower, user_context)
        
        # Document-related queries
        elif any(keyword in message_lower for keyword in ["document", "upload", "file", "receipt"]):
            return self._generate_document_response(message_lower, document_context)
        
        # General financial advice
        elif any(keyword in message_lower for keyword in ["advice", "recommend", "suggest", "optimize"]):
            return self._generate_advice_response(message_lower, user_context)
        
        # Default response
        else:
            return self._generate_default_response(message_lower, user_context)
    
    def _generate_tax_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate tax-related response"""
        
        tax_records = context.get("tax_records", [])
        transactions = context.get("transactions", [])
        
        if not tax_records:
            return "I don't see any tax calculations in your account yet. Would you like me to help you calculate your tax liability based on your uploaded documents?"
        
        latest_tax = tax_records[0]
        total_income = sum(record.get("total_income", 0) for record in tax_records)
        total_tax = sum(record.get("predicted_tax", 0) for record in tax_records)
        
        if "latest" in message or "recent" in message:
            return f"Your latest tax calculation for FY {latest_tax.get('fiscal_year', 'N/A')} shows:\n\n" \
                   f"• Total Income: ₹{latest_tax.get('total_income', 0):,.0f}\n" \
                   f"• Predicted Tax: ₹{latest_tax.get('predicted_tax', 0):,.0f}\n" \
                   f"• Confidence: {latest_tax.get('confidence_score', 0):.1%}\n\n" \
                   f"Based on {latest_tax.get('transactions_analyzed', 0)} transactions analyzed."
        
        elif "total" in message or "summary" in message:
            return f"Here's your tax summary across all calculations:\n\n" \
                   f"• Total Income: ₹{total_income:,.0f}\n" \
                   f"• Total Tax Liability: ₹{total_tax:,.0f}\n" \
                   f"• Effective Tax Rate: {(total_tax/total_income*100) if total_income > 0 else 0:.1f}%\n" \
                   f"• Tax Records: {len(tax_records)}\n\n" \
                   f"Would you like me to suggest tax optimization strategies?"
        
        elif "save" in message or "optimize" in message:
            return "Here are some tax optimization suggestions based on your data:\n\n" \
                   f"• Maximize 80C deductions (up to ₹1.5L)\n" \
                   f"• Consider health insurance for 80D benefits\n" \
                   f"• Keep all investment receipts for filing\n" \
                   f"• Plan quarterly tax payments to avoid penalties\n\n" \
                   f"Your current effective rate is {(total_tax/total_income*100) if total_income > 0 else 0:.1f}%."
        
        else:
            return f"I can help you with tax-related questions! You have {len(tax_records)} tax calculations on record. " \
                   f"Ask me about your latest tax calculation, total tax summary, or tax optimization strategies."
    
    def _generate_transaction_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate transaction-related response"""
        
        transactions = context.get("transactions", [])
        
        if not transactions:
            return "I don't see any transactions in your account yet. Please upload your financial documents so I can analyze your transactions."
        
        total_amount = sum(abs(txn.get("amount", 0)) for txn in transactions)
        categories = {}
        for txn in transactions:
            cat = txn.get("category", "other")
            categories[cat] = categories.get(cat, 0) + abs(txn.get("amount", 0))
        
        top_category = max(categories.items(), key=lambda x: x[1]) if categories else ("other", 0)
        
        if "total" in message or "summary" in message:
            return f"Transaction Summary:\n\n" \
                   f"• Total Transactions: {len(transactions)}\n" \
                   f"• Total Amount: ₹{total_amount:,.0f}\n" \
                   f"• Top Category: {top_category[0].title()} (₹{top_category[1]:,.0f})\n" \
                   f"• Average Transaction: ₹{total_amount/len(transactions):,.0f}\n\n" \
                   f"Categories: {', '.join([f'{k.title()}: ₹{v:,.0f}' for k, v in list(categories.items())[:3]])}"
        
        elif "category" in message or "breakdown" in message:
            category_list = "\n".join([f"• {k.title()}: ₹{v:,.0f}" for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)])
            return f"Transaction Breakdown by Category:\n\n{category_list}\n\n" \
                   f"Total across all categories: ₹{total_amount:,.0f}"
        
        elif "recent" in message or "latest" in message:
            recent_txns = transactions[:5]
            txn_list = "\n".join([f"• {txn.get('description', 'N/A')}: ₹{abs(txn.get('amount', 0)):,.0f} ({txn.get('category', 'other')})" for txn in recent_txns])
            return f"Your 5 most recent transactions:\n\n{txn_list}\n\n" \
                   f"Total recent activity: ₹{sum(abs(txn.get('amount', 0)) for txn in recent_txns):,.0f}"
        
        else:
            return f"I can analyze your {len(transactions)} transactions totaling ₹{total_amount:,.0f}. " \
                   f"Ask me about transaction summaries, category breakdowns, or recent activity."
    
    def _generate_anomaly_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate anomaly-related response"""
        
        anomaly_reports = context.get("anomaly_reports", [])
        transactions = context.get("transactions", [])
        
        if not anomaly_reports:
            return "No anomaly scans have been performed yet. Upload your documents and run an anomaly scan to detect suspicious transactions."
        
        latest_report = anomaly_reports[0]
        total_anomalies = sum(report.get("anomalous_transactions", 0) for report in anomaly_reports)
        high_risk_txns = [txn for txn in transactions if txn.get("anomaly_score", 0) >= 0.7]
        
        if "latest" in message or "recent" in message:
            return f"Latest Anomaly Scan Results:\n\n" \
                   f"• Total Transactions Scanned: {latest_report.get('total_transactions', 0)}\n" \
                   f"• Anomalies Detected: {latest_report.get('anomalous_transactions', 0)}\n" \
                   f"• Anomaly Rate: {latest_report.get('anomaly_rate', 0):.1f}%\n" \
                   f"• High Risk: {latest_report.get('high_risk_count', 0)}\n" \
                   f"• Flagged Amount: ₹{latest_report.get('total_flagged_amount', 0):,.0f}\n\n" \
                   f"Would you like me to explain the specific anomalies found?"
        
        elif "high" in message and "risk" in message:
            if high_risk_txns:
                risk_list = "\n".join([f"• ₹{abs(txn.get('amount', 0)):,.0f} - {txn.get('merchant', 'Unknown')} (Score: {txn.get('anomaly_score', 0):.2f})" for txn in high_risk_txns[:5]])
                return f"High Risk Transactions (Score ≥ 0.7):\n\n{risk_list}\n\n" \
                       f"Total high-risk transactions: {len(high_risk_txns)}\n" \
                       f"These transactions require immediate review."
            else:
                return "Great news! No high-risk transactions detected in your recent data. Your transaction patterns appear normal."
        
        elif "summary" in message or "total" in message:
            return f"Anomaly Detection Summary:\n\n" \
                   f"• Total Scans Performed: {len(anomaly_reports)}\n" \
                   f"• Total Anomalies Found: {total_anomalies}\n" \
                   f"• High-Risk Transactions: {len(high_risk_txns)}\n" \
                   f"• Latest Scan Date: {latest_report.get('created_at', 'N/A')}\n\n" \
                   f"Your account security status: {'⚠️ Needs Attention' if len(high_risk_txns) > 0 else '✅ Secure'}"
        
        else:
            return f"I've analyzed {len(anomaly_reports)} anomaly reports for your account. " \
                   f"Ask me about the latest scan results, high-risk transactions, or overall security summary."
    
    def _generate_document_response(self, message: str, document_context: List[Dict[str, Any]]) -> str:
        """Generate document-related response"""
        
        if not document_context:
            return "No specific documents are pinned to this conversation. You can pin documents to get detailed analysis of their contents."
        
        doc_info = []
        for doc in document_context:
            transactions_count = len(doc.get("parsed_data", {}).get("transactions", []))
            doc_info.append(f"• {doc.get('filename', 'Unknown')}: {transactions_count} transactions, Status: {doc.get('status', 'unknown')}")
        
        doc_list = "\n".join(doc_info)
        
        return f"Pinned Documents Analysis:\n\n{doc_list}\n\n" \
               f"I can answer questions about the contents, transactions, or processing status of these documents. " \
               f"What would you like to know?"
    
    def _generate_advice_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate financial advice response"""
        
        tax_records = context.get("tax_records", [])
        transactions = context.get("transactions", [])
        anomaly_reports = context.get("anomaly_reports", [])
        
        advice = ["Based on your financial data, here are my recommendations:\n"]
        
        # Tax advice
        if tax_records:
            latest_tax = tax_records[0]
            if latest_tax.get("predicted_tax", 0) > 50000:
                advice.append("💰 Tax Planning: Consider quarterly tax payments to avoid penalties")
            
            deduction_ratio = latest_tax.get("total_deductions", 0) / latest_tax.get("total_income", 1)
            if deduction_ratio < 0.1:
                advice.append("📊 Deductions: Maximize your 80C and 80D deductions to save tax")
        
        # Transaction advice
        if transactions:
            cash_txns = [txn for txn in transactions if "cash" in txn.get("category", "").lower()]
            if len(cash_txns) > len(transactions) * 0.3:
                advice.append("💳 Digital Payments: Consider using digital payments for better tracking")
        
        # Security advice
        if anomaly_reports:
            latest_anomaly = anomaly_reports[0]
            if latest_anomaly.get("anomaly_rate", 0) > 10:
                advice.append("🔒 Security: Review your transaction patterns - high anomaly rate detected")
        
        # General advice
        advice.extend([
            "📋 Documentation: Keep all receipts and investment proofs organized",
            "📈 Regular Reviews: Monitor your financial data monthly for better insights",
            "🤖 AI Assistance: Use this chatbot regularly to stay on top of your finances"
        ])
        
        return "\n\n".join(advice)
    
    def _generate_default_response(self, message: str, context: Dict[str, Any]) -> str:
        """Generate default response"""
        
        tax_count = len(context.get("tax_records", []))
        txn_count = len(context.get("transactions", []))
        anomaly_count = len(context.get("anomaly_reports", []))
        
        return f"I'm your AI financial assistant! I can help you with:\n\n" \
               f"📊 Tax Analysis ({tax_count} records available)\n" \
               f"💳 Transaction Insights ({txn_count} transactions)\n" \
               f"🔍 Anomaly Detection ({anomaly_count} scans performed)\n" \
               f"📋 Document Analysis\n" \
               f"💡 Financial Advice\n\n" \
               f"Try asking me about your latest tax calculation, transaction summary, or anomaly scan results!"
    
    async def _store_conversation(
        self,
        user_id: str,
        message: str,
        response: str,
        context_documents: List[str]
    ):
        """Store conversation in database"""
        
        try:
            db = await get_database()
            
            chat_message = ChatMessage(
                user_id=ObjectId(user_id),
                message=message,
                response=response,
                context_documents=[ObjectId(doc_id) for doc_id in context_documents]
            )
            
            await db.chat_messages.insert_one(chat_message.dict(by_alias=True))
            
        except Exception as e:
            print(f"Error storing conversation: {e}")
    
    async def get_conversation_history(
        self, 
        user_id: str, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history for user"""
        
        try:
            db = await get_database()
            
            messages = await db.chat_messages.find(
                {"user_id": ObjectId(user_id)}
            ).sort("created_at", -1).limit(limit).to_list(limit)
            
            # Convert ObjectIds to strings
            for msg in messages:
                msg["_id"] = str(msg["_id"])
                msg["user_id"] = str(msg["user_id"])
                msg["context_documents"] = [str(doc_id) for doc_id in msg["context_documents"]]
                if isinstance(msg.get("created_at"), datetime):
                    msg["created_at"] = msg["created_at"].isoformat()
            
            return list(reversed(messages))  # Return oldest first
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    async def pin_document(
        self, 
        user_id: str, 
        document_id: str
    ) -> Dict[str, Any]:
        """Pin document for conversation context"""
        
        try:
            db = await get_database()
            
            # Verify document ownership
            document = await db.documents.find_one({
                "_id": ObjectId(document_id),
                "user_id": ObjectId(user_id)
            })
            
            if not document:
                return {"success": False, "message": "Document not found"}
            
            return {
                "success": True,
                "message": f"Document '{document['filename']}' pinned to conversation",
                "document": {
                    "id": str(document["_id"]),
                    "filename": document["filename"],
                    "type": document["type"],
                    "status": document["status"]
                }
            }
            
        except Exception as e:
            print(f"Error pinning document: {e}")
            return {"success": False, "message": "Failed to pin document"}