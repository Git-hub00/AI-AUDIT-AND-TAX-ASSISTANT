import uuid
import os
from typing import Dict, List, Optional, Tuple
from .command_parser import CommandParser
from .csv_processor import CSVProcessor

class CSVAgent:
    def __init__(self):
        self.command_parser = CommandParser()
        self.csv_processor = CSVProcessor()
        self.sessions = {}  # Store session data temporarily
        self.temp_dir = "temp_files"
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def process_file_upload(self, file_content: bytes, filename: str) -> Dict:
        """Process uploaded CSV file and return analysis"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Read and analyze CSV
            df, analysis = self.csv_processor.read_csv(file_content)
            
            # Store in session
            self.sessions[session_id] = {
                'dataframe': df,
                'filename': filename,
                'analysis': analysis,
                'original_file_content': file_content
            }
            
            # Generate summary message
            summary = self._generate_file_summary(analysis, filename)
            
            return {
                'success': True,
                'session_id': session_id,
                'message': summary,
                'analysis': analysis,
                'preview': self.csv_processor.get_preview_data(df, limit=3)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error processing file: {str(e)}",
                'error': str(e)
            }
    
    def process_command(self, session_id: str, command: str) -> Dict:
        """Process user command and return filtered data"""
        if session_id not in self.sessions:
            return {
                'success': False,
                'message': "Session not found. Please upload a CSV file first."
            }
        
        try:
            session_data = self.sessions[session_id]
            df = session_data['dataframe']
            
            # Parse command
            filters = self.command_parser.parse_command(command)
            
            # Apply filters
            filtered_df = self.csv_processor.filter_data(df, filters)
            
            if filtered_df.empty:
                return {
                    'success': False,
                    'message': "No transactions match your criteria. Please try a different filter."
                }
            
            # Generate preview
            preview = self.csv_processor.get_preview_data(filtered_df, limit=5)
            
            # Generate confirmation message with debug info
            transaction_counts = filtered_df['transaction_type'].value_counts().to_dict() if 'transaction_type' in filtered_df.columns else {}
            confirmation_msg = self.command_parser.generate_confirmation_message(
                filters, len(filtered_df)
            )
            
            # Add debug info about transaction types
            if transaction_counts:
                debug_info = f"\n\nTransaction breakdown: {transaction_counts}"
                confirmation_msg += debug_info
            
            # Store filtered data in session
            session_data['filtered_data'] = filtered_df
            session_data['current_filters'] = filters
            
            # Auto-generate files for download if separation is requested
            files_info = None
            if filters.get('separate_output') or 'separat' in command.lower():
                files_result = self.generate_download_files(session_id)
                if files_result.get('success'):
                    files_info = files_result.get('files', [])
                    confirmation_msg += "\n\n📁 Files generated and ready for download!"
            
            result = {
                'success': True,
                'message': confirmation_msg,
                'preview': preview,
                'count': len(filtered_df),
                'filters_applied': filters,
                'ready_for_download': True
            }
            
            if files_info:
                result['files'] = files_info
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error processing command: {str(e)}",
                'error': str(e)
            }
    
    def generate_download_files(self, session_id: str) -> Dict:
        """Generate CSV files for download"""
        if session_id not in self.sessions:
            return {
                'success': False,
                'message': "Session not found."
            }
        
        try:
            session_data = self.sessions[session_id]
            
            if 'filtered_data' not in session_data:
                # Use original dataframe if no filtered data
                filtered_df = session_data.get('dataframe')
                filters = {'separate_output': True}  # Default to separation
            else:
                filtered_df = session_data['filtered_data']
                filters = session_data.get('current_filters', {})
            
            if filtered_df is None or filtered_df.empty:
                return {
                    'success': False,
                    'message': "No data available for file generation."
                }
            
            # Generate CSV files
            csv_files = self.csv_processor.generate_csv_files(filtered_df, filters)
            
            # Save files temporarily and return file info
            file_info = []
            for filename, csv_content in csv_files.items():
                file_path = os.path.join(self.temp_dir, f"{session_id}_{filename}")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                
                # Count rows in this specific file
                rows_count = len(csv_content.split('\n')) - 1  # Subtract header
                
                file_info.append({
                    'filename': filename,
                    'path': file_path,
                    'size': len(csv_content.encode('utf-8')),
                    'rows': rows_count
                })
            
            # Store file info in session
            session_data['generated_files'] = file_info
            
            return {
                'success': True,
                'message': f"Generated {len(file_info)} file(s) successfully!",
                'files': file_info,
                'download_ready': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error generating files: {str(e)}",
                'error': str(e)
            }
    
    def get_file_content(self, session_id: str, filename: str) -> Optional[bytes]:
        """Get file content for download"""
        if session_id not in self.sessions:
            return None
        
        session_data = self.sessions[session_id]
        if 'generated_files' not in session_data:
            return None
        
        # Find file
        for file_info in session_data['generated_files']:
            if file_info['filename'] == filename:
                try:
                    with open(file_info['path'], 'rb') as f:
                        return f.read()
                except:
                    return None
        
        return None
    
    def cleanup_session(self, session_id: str):
        """Clean up session data and temporary files"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            
            # Remove temporary files
            if 'generated_files' in session_data:
                for file_info in session_data['generated_files']:
                    try:
                        os.remove(file_info['path'])
                    except:
                        pass
            
            # Remove session
            del self.sessions[session_id]
    
    def _generate_file_summary(self, analysis: Dict, filename: str) -> str:
        """Generate user-friendly file summary"""
        total_rows = analysis.get('total_rows', 0)
        date_range = analysis.get('date_range')
        transaction_types = analysis.get('transaction_types', {})
        
        summary_parts = [
            f"📄 Successfully uploaded '{filename}'",
            f"📊 Found {total_rows} transactions"
        ]
        
        if date_range:
            summary_parts.append(f"📅 Date range: {date_range['start']} to {date_range['end']}")
        
        if transaction_types:
            type_summary = []
            for txn_type, count in transaction_types.items():
                type_summary.append(f"{count} {txn_type}s")
            summary_parts.append(f"💳 Transaction types: {', '.join(type_summary)}")
        
        summary_parts.extend([
            "",
            "🤖 Now you can ask me to filter the data:",
            "• 'Show only credit transactions'",
            "• 'List debits above ₹2000'",
            "• 'Give credits and debits separately'",
            "• 'Show transactions above ₹5000'",
            "",
            "What would you like me to do with this data?"
        ])
        
        return "\n".join(summary_parts)
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            return {
                'filename': session_data.get('filename'),
                'total_rows': len(session_data.get('dataframe', [])),
                'has_filtered_data': 'filtered_data' in session_data,
                'has_generated_files': 'generated_files' in session_data
            }
        return None