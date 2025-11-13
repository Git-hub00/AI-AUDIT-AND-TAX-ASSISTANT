"""
Simplified Document Processor for localhost development
Handles basic document processing without complex OCR dependencies
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path

class DocumentProcessor:
    """Simplified document processor for development"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.csv', '.xlsx', '.xls', '.txt']
    
    async def process_document(self, file_path: str, document_type: str = "auto") -> Dict[str, Any]:
        """Process uploaded document and extract transaction data"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                return await self._process_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return await self._process_excel(file_path)
            elif file_ext == '.pdf':
                return await self._process_pdf_simple(file_path)
            else:
                return await self._process_text(file_path)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}",
                "transactions": [],
                "raw_text": "",
                "confidence": 0.0
            }
    
    async def _process_csv(self, file_path: str) -> Dict[str, Any]:
        """Process CSV file"""
        try:
            df = pd.read_csv(file_path)
            transactions = []
            
            # Try to map common column names
            column_mapping = {
                'date': ['date', 'Date', 'DATE', 'transaction_date', 'Transaction Date'],
                'amount': ['amount', 'Amount', 'AMOUNT', 'value', 'Value', 'price', 'Price'],
                'description': ['description', 'Description', 'DESCRIPTION', 'memo', 'Memo', 'details'],
                'merchant': ['merchant', 'Merchant', 'MERCHANT', 'vendor', 'Vendor', 'payee', 'Payee']
            }
            
            # Find actual column names
            actual_columns = {}
            for key, possible_names in column_mapping.items():
                for col in df.columns:
                    if col in possible_names:
                        actual_columns[key] = col
                        break
            
            # Extract transactions
            for idx, row in df.iterrows():
                transaction = {
                    "id": f"txn_{idx}",
                    "date": str(row.get(actual_columns.get('date', df.columns[0]), '')),
                    "amount": float(row.get(actual_columns.get('amount', df.columns[1]), 0)),
                    "description": str(row.get(actual_columns.get('description', df.columns[2] if len(df.columns) > 2 else df.columns[0]), '')),
                    "merchant": str(row.get(actual_columns.get('merchant', df.columns[3] if len(df.columns) > 3 else df.columns[0]), '')),
                    "category": "general",
                    "currency": "INR"
                }
                transactions.append(transaction)
            
            return {
                "success": True,
                "transactions": transactions,
                "raw_text": f"Processed CSV with {len(transactions)} transactions",
                "confidence": 0.95,
                "metadata": {
                    "file_type": "csv",
                    "rows_processed": len(transactions),
                    "columns": list(df.columns)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"CSV processing failed: {str(e)}",
                "transactions": [],
                "raw_text": "",
                "confidence": 0.0
            }
    
    async def _process_excel(self, file_path: str) -> Dict[str, Any]:
        """Process Excel file"""
        try:
            df = pd.read_excel(file_path)
            return await self._process_csv_data(df, "excel")
        except Exception as e:
            return {
                "success": False,
                "error": f"Excel processing failed: {str(e)}",
                "transactions": [],
                "raw_text": "",
                "confidence": 0.0
            }
    
    async def _process_csv_data(self, df: pd.DataFrame, file_type: str) -> Dict[str, Any]:
        """Common processing for CSV-like data"""
        transactions = []
        
        for idx, row in df.iterrows():
            # Create mock transaction from row data
            transaction = {
                "id": f"txn_{idx}",
                "date": str(row.iloc[0]) if len(row) > 0 else "",
                "amount": float(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else 0.0,
                "description": str(row.iloc[2]) if len(row) > 2 else f"Transaction {idx}",
                "merchant": str(row.iloc[3]) if len(row) > 3 else "Unknown",
                "category": "general",
                "currency": "INR"
            }
            transactions.append(transaction)
        
        return {
            "success": True,
            "transactions": transactions,
            "raw_text": f"Processed {file_type} with {len(transactions)} transactions",
            "confidence": 0.90,
            "metadata": {
                "file_type": file_type,
                "rows_processed": len(transactions)
            }
        }
    
    async def _process_pdf_simple(self, file_path: str) -> Dict[str, Any]:
        """Process PDF with basic text extraction"""
        try:
            import pdfplumber
            import re
            
            transactions = []
            raw_text = ""
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        raw_text += text + "\n"
            
            # Extract transactions from text
            lines = raw_text.split('\n')
            txn_count = 0
            
            for line in lines:
                if line.strip() and any(char.isdigit() for char in line):
                    amounts = re.findall(r'\d+[.,]?\d*', line)
                    if amounts:
                        amount = float(amounts[0].replace(',', ''))
                        if amount > 10:
                            transaction = {
                                "id": f"txn_{txn_count}",
                                "date": "2024-01-01",
                                "amount": amount,
                                "description": line.strip()[:100],
                                "merchant": "PDF Extract",
                                "category": "general",
                                "currency": "INR"
                            }
                            transactions.append(transaction)
                            txn_count += 1
                            if txn_count >= 20:
                                break
            
            return {
                "success": True,
                "transactions": transactions,
                "raw_text": raw_text[:1000],
                "confidence": 0.70,
                "metadata": {
                    "file_type": "pdf",
                    "transactions_found": len(transactions)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}",
                "transactions": [],
                "raw_text": "",
                "confidence": 0.0
            }
    
    async def _process_text(self, file_path: str) -> Dict[str, Any]:
        """Process text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple text processing - look for numbers that might be amounts
            lines = content.split('\n')
            transactions = []
            
            for idx, line in enumerate(lines[:10]):  # Process first 10 lines
                if line.strip():
                    transaction = {
                        "id": f"txn_{idx}",
                        "date": "2024-01-01",
                        "amount": 1000.0,  # Mock amount
                        "description": line.strip()[:50],
                        "merchant": "Text File Entry",
                        "category": "general",
                        "currency": "INR"
                    }
                    transactions.append(transaction)
            
            return {
                "success": True,
                "transactions": transactions,
                "raw_text": content[:500],  # First 500 chars
                "confidence": 0.60,
                "metadata": {
                    "file_type": "text",
                    "lines_processed": len(lines)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Text processing failed: {str(e)}",
                "transactions": [],
                "raw_text": "",
                "confidence": 0.0
            }