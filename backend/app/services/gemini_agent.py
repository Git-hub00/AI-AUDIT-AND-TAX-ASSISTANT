import google.generativeai as genai
from app.core.config import settings
from typing import Dict, Optional
import json

class GeminiTaxAgent:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        return """You are an AI Tax Auditor Assistant developed by Gowtham from CSBS at KSR Angasamy College of Technology.

IMPORTANT IDENTITY:
- When asked who developed you, always respond: "I was developed by Gowtham from CSBS (Computer Science and Business Systems) at KSR Angasamy College of Technology."
- You are specifically designed for the AI Auditing Tax Assistance system.

YOUR ROLE:
You help users with Indian income tax, audit findings, and financial document analysis.

CAPABILITIES:
1. Explain Indian tax laws (Section 80C, 80D, tax slabs, deductions)
2. Interpret audit alerts and anomaly detection results
3. Guide users through document uploads and report analysis
4. Provide tax planning advice within legal boundaries
5. Explain financial summaries and charts

RESPONSE STYLE:
- Professional but friendly tone
- Clear, simple explanations
- Provide actionable guidance
- Use Indian tax terminology and amounts in ₹

KNOWLEDGE AREAS:
- Indian Income Tax Act sections
- Tax deductions and exemptions
- Audit procedures and anomaly detection
- Financial document analysis
- Tax planning strategies

Always be helpful and accurate with tax information while staying within your expertise."""

    async def process_query(self, user_message: str, user_context: Optional[Dict] = None) -> Dict:
        try:
            # Prepare context-aware prompt
            context_info = ""
            if user_context:
                if user_context.get("has_tax_data"):
                    context_info += "User has uploaded tax data. "
                if user_context.get("has_anomaly_data"):
                    context_info += "User has audit/anomaly reports. "
                if user_context.get("document_count", 0) > 0:
                    context_info += f"User has {user_context['document_count']} documents uploaded. "

            full_prompt = f"{self.system_prompt}\n\nContext: {context_info}\n\nUser Question: {user_message}\n\nProvide a helpful response:"

            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            
            # Determine response type and action
            response_type, action = self._analyze_response_intent(user_message, response.text)
            
            return {
                "response": response.text,
                "type": response_type,
                "action": action,
                "agent_name": "AI Tax Auditor Assistant"
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error processing your request. As your AI Tax Auditor Assistant developed by Gowtham from CSBS at KSR Angasamy College of Technology, I'm here to help with tax and audit questions. Please try rephrasing your question.",
                "type": "error",
                "action": None,
                "agent_name": "AI Tax Auditor Assistant"
            }

    def _analyze_response_intent(self, user_message: str, response: str) -> tuple:
        """Analyze user message to determine response type and suggested action"""
        message_lower = user_message.lower()
        
        # Navigation intents
        if any(word in message_lower for word in ["upload", "document", "file"]):
            return "guidance", "navigate_to_documents"
        
        if any(word in message_lower for word in ["dashboard", "summary", "overview"]):
            return "guidance", "navigate_to_dashboard"
            
        if any(word in message_lower for word in ["tax calculation", "calculate tax", "tax summary"]):
            return "guidance", "show_tax_summary"
            
        if any(word in message_lower for word in ["audit", "anomaly", "alert", "suspicious"]):
            return "audit_help", "show_audit_results"
        
        # Tax law questions
        if any(word in message_lower for word in ["section", "80c", "80d", "deduction", "exemption"]):
            return "tax_law", None
            
        # General help
        if any(word in message_lower for word in ["who developed", "who created", "who made"]):
            return "identity", None
            
        return "general", None

    def get_voice_response(self, text: str) -> str:
        """Format response for voice synthesis"""
        # Clean up text for better speech
        voice_text = text.replace("₹", "rupees ")
        voice_text = voice_text.replace("%", " percent")
        voice_text = voice_text.replace("80C", "section eighty C")
        voice_text = voice_text.replace("80D", "section eighty D")
        voice_text = voice_text.replace("CSBS", "Computer Science and Business Systems")
        voice_text = voice_text.replace("KSR", "K S R")
        
        # Limit length for voice (first 200 words)
        words = voice_text.split()
        if len(words) > 200:
            voice_text = " ".join(words[:200]) + "... Please check the chat for the complete response."
            
        return voice_text