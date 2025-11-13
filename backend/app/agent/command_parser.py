import re
from typing import Dict, List, Optional

class CommandParser:
    def __init__(self):
        self.patterns = {
            'credit': r'\b(credit|credits|credited|deposit|deposits|deposited|income|received)\b',
            'debit': r'\b(debit|debits|debited|withdrawal|withdrawals|expense|expenses|spent|payment|payments)\b',
            'amount_above': r'\b(above|over|greater than|more than|>\s*)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\b',
            'amount_below': r'\b(below|under|less than|<\s*)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\b',
            'amount_equal': r'\b(equal to|exactly|=\s*)\s*₹?\s*(\d+(?:,\d+)*(?:\.\d+)?)\b',
            'both': r'\b(both|all|everything|complete|full)\b',
            'separate': r'\b(separate|separately|split|divide)\b',
            'date_range': r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*(to|and|-)\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'
        }
    
    def parse_command(self, command: str) -> Dict:
        """Parse natural language command into structured filters"""
        command_lower = command.lower()
        
        filters = {
            'transaction_type': None,  # 'credit', 'debit', 'both'
            'amount_filter': None,     # {'type': 'above/below/equal', 'value': amount}
            'separate_output': False,  # True if user wants separate files
            'date_range': None,        # {'start': date, 'end': date}
            'description': command     # Original command for confirmation
        }
        
        # Parse transaction type
        if re.search(self.patterns['credit'], command_lower) and re.search(self.patterns['debit'], command_lower):
            filters['transaction_type'] = 'both'
        elif re.search(self.patterns['credit'], command_lower):
            filters['transaction_type'] = 'credit'
        elif re.search(self.patterns['debit'], command_lower):
            filters['transaction_type'] = 'debit'
        elif re.search(self.patterns['both'], command_lower):
            filters['transaction_type'] = 'both'
        
        # Parse amount filters
        amount_above = re.search(self.patterns['amount_above'], command_lower)
        amount_below = re.search(self.patterns['amount_below'], command_lower)
        amount_equal = re.search(self.patterns['amount_equal'], command_lower)
        
        if amount_above:
            amount_str = amount_above.group(2).replace(',', '')
            filters['amount_filter'] = {'type': 'above', 'value': float(amount_str)}
        elif amount_below:
            amount_str = amount_below.group(2).replace(',', '')
            filters['amount_filter'] = {'type': 'below', 'value': float(amount_str)}
        elif amount_equal:
            amount_str = amount_equal.group(2).replace(',', '')
            filters['amount_filter'] = {'type': 'equal', 'value': float(amount_str)}
        
        # Check for separate output request
        if (re.search(self.patterns['separate'], command_lower) or 
            ('credit' in command_lower and 'debit' in command_lower and 
             any(word in command_lower for word in ['both', 'and', 'separate', 'split']))):
            filters['separate_output'] = True
        
        # Parse date range (basic implementation)
        date_match = re.search(self.patterns['date_range'], command_lower)
        if date_match:
            filters['date_range'] = {
                'start': date_match.group(1),
                'end': date_match.group(3)
            }
        
        return filters
    
    def generate_confirmation_message(self, filters: Dict, preview_count: int) -> str:
        """Generate user-friendly confirmation message"""
        parts = []
        
        # Transaction type
        if filters['transaction_type'] == 'credit':
            parts.append("credit transactions")
        elif filters['transaction_type'] == 'debit':
            parts.append("debit transactions")
        elif filters['transaction_type'] == 'both':
            parts.append("all transactions")
        else:
            parts.append("transactions")
        
        # Amount filter
        if filters['amount_filter']:
            amount_filter = filters['amount_filter']
            if amount_filter['type'] == 'above':
                parts.append(f"above ₹{amount_filter['value']:,.0f}")
            elif amount_filter['type'] == 'below':
                parts.append(f"below ₹{amount_filter['value']:,.0f}")
            elif amount_filter['type'] == 'equal':
                parts.append(f"equal to ₹{amount_filter['value']:,.0f}")
        
        # Date range
        if filters['date_range']:
            parts.append(f"from {filters['date_range']['start']} to {filters['date_range']['end']}")
        
        filter_description = " ".join(parts)
        
        if filters['separate_output']:
            return f"I found {preview_count} {filter_description}. I'll create separate files for credits and debits. Proceed?"
        else:
            return f"I found {preview_count} {filter_description}. Generate CSV file?"