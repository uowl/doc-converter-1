import csv
import os
import datetime
from typing import Dict, List

class FailedConversionsTracker:
    def __init__(self, csv_file_path="failed_conversions.csv"):
        self.csv_file_path = csv_file_path
        self.csv_headers = [
            'timestamp',
            'filename',
            'file_size_bytes',
            'error_type',
            'error_message',
            'attempt_count'
        ]
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_file_path):
            with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()
    
    def add_failed_conversion(self, filename: str, error_type: str, error_message: str, 
                             file_size_bytes: int = None, attempt_count: int = 1):
        """Add a failed conversion record to the CSV file."""
        try:
            record = {
                'timestamp': datetime.datetime.now().isoformat(),
                'filename': filename,
                'file_size_bytes': file_size_bytes or 0,
                'error_type': error_type,
                'error_message': error_message,
                'attempt_count': attempt_count
            }
            
            with open(self.csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writerow(record)
                
        except Exception as e:
            print(f"Error writing to failed conversions CSV: {str(e)}")
    
    def get_failed_conversions(self) -> List[Dict]:
        """Read all failed conversions from the CSV file."""
        failed_conversions = []
        try:
            if os.path.exists(self.csv_file_path):
                with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        failed_conversions.append(row)
        except Exception as e:
            print(f"Error reading failed conversions CSV: {str(e)}")
        
        return failed_conversions
    
    def get_failed_conversions_by_filename(self, filename: str) -> List[Dict]:
        """Get failed conversion records for a specific filename."""
        all_failures = self.get_failed_conversions()
        return [failure for failure in all_failures if failure['filename'] == filename]
    
    def get_failed_conversions_by_error_type(self, error_type: str) -> List[Dict]:
        """Get failed conversion records for a specific error type."""
        all_failures = self.get_failed_conversions()
        return [failure for failure in all_failures if failure['error_type'] == error_type]
    
    def get_recent_failures(self, hours: int = 24) -> List[Dict]:
        """Get failed conversions from the last N hours."""
        all_failures = self.get_failed_conversions()
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        
        recent_failures = []
        for failure in all_failures:
            try:
                failure_time = datetime.datetime.fromisoformat(failure['timestamp'])
                if failure_time >= cutoff_time:
                    recent_failures.append(failure)
            except ValueError:
                # Skip records with invalid timestamps
                continue
        
        return recent_failures
    
    def get_failure_summary(self) -> Dict:
        """Get a summary of failed conversions."""
        all_failures = self.get_failed_conversions()
        
        if not all_failures:
            return {
                'total_failures': 0,
                'unique_files': 0,
                'error_types': {},
                'recent_failures_24h': 0
            }
        
        # Count unique files
        unique_files = set(failure['filename'] for failure in all_failures)
        
        # Count error types
        error_types = {}
        for failure in all_failures:
            error_type = failure['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Count recent failures
        recent_failures = len(self.get_recent_failures(24))
        
        return {
            'total_failures': len(all_failures),
            'unique_files': len(unique_files),
            'error_types': error_types,
            'recent_failures_24h': recent_failures
        }
    
    def clear_old_records(self, days: int = 30):
        """Clear failed conversion records older than specified days."""
        try:
            all_failures = self.get_failed_conversions()
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
            
            recent_failures = []
            for failure in all_failures:
                try:
                    failure_time = datetime.datetime.fromisoformat(failure['timestamp'])
                    if failure_time >= cutoff_time:
                        recent_failures.append(failure)
                except ValueError:
                    # Skip records with invalid timestamps
                    continue
            
            # Rewrite the CSV with only recent records
            with open(self.csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()
                writer.writerows(recent_failures)
                
        except Exception as e:
            print(f"Error clearing old records: {str(e)}")
    
    def export_failures_to_csv(self, output_path: str, filters: Dict = None):
        """Export failed conversions to a new CSV file with optional filters."""
        try:
            all_failures = self.get_failed_conversions()
            
            # Apply filters if provided
            if filters:
                filtered_failures = []
                for failure in all_failures:
                    include = True
                    for key, value in filters.items():
                        if key in failure and failure[key] != value:
                            include = False
                            break
                    if include:
                        filtered_failures.append(failure)
                all_failures = filtered_failures
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_headers)
                writer.writeheader()
                writer.writerows(all_failures)
                
        except Exception as e:
            print(f"Error exporting failures: {str(e)}") 