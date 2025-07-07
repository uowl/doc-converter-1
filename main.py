import time
import os
import logging
from blob_monitor import BlobMonitor
from document_converter import DocumentConverter
from failed_conversions import FailedConversionsTracker
from config import POLLING_INTERVAL, TRIGGER_FILE_PATTERN

class DocumentConverterApp:
    def __init__(self):
        self.blob_monitor = BlobMonitor()
        self.document_converter = DocumentConverter()
        self.failed_tracker = FailedConversionsTracker()
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('doc_converter.log'),
                logging.StreamHandler()
            ]
        )
    
    def process_documents(self):
        """Process all documents when trigger file is found."""
        try:
            self.logger.info("Starting document processing...")
            
            # Get list of documents to convert
            documents = self.blob_monitor.get_documents_to_convert()
            
            if not documents:
                self.logger.info("No documents found to convert.")
                return
            
            self.logger.info(f"Found {len(documents)} documents to convert.")
            
            # Process each document
            for document_name in documents:
                self._process_single_document(document_name)
            
            # Delete the trigger file after processing
            self.blob_monitor.delete_trigger_file()
            
            # Display failure summary after processing
            self._display_failure_summary()
            
            self.logger.info("Document processing completed.")
            
        except Exception as e:
            self.logger.error(f"Error in document processing: {str(e)}")
    
    def _display_failure_summary(self):
        """Display a summary of failed conversions."""
        try:
            summary = self.failed_tracker.get_failure_summary()
            
            if summary['total_failures'] > 0:
                self.logger.info("=== FAILED CONVERSIONS SUMMARY ===")
                self.logger.info(f"Total failures: {summary['total_failures']}")
                self.logger.info(f"Unique files with failures: {summary['unique_files']}")
                self.logger.info(f"Failures in last 24h: {summary['recent_failures_24h']}")
                
                if summary['error_types']:
                    self.logger.info("Error types breakdown:")
                    for error_type, count in summary['error_types'].items():
                        self.logger.info(f"  {error_type}: {count}")
                
                self.logger.info("Check failed_conversions.csv for details")
                self.logger.info("=========================================")
            else:
                self.logger.info("✓ No failed conversions recorded")
                
        except Exception as e:
            self.logger.error(f"Error displaying failure summary: {str(e)}")
    
    def _process_single_document(self, document_name):
        """Process a single document."""
        try:
            self.logger.info(f"Processing document: {document_name}")
            
            # Create temporary file path
            temp_file_path = os.path.join("temp", document_name)
            os.makedirs("temp", exist_ok=True)
            
            # Get file size for tracking
            file_size = 0
            try:
                if os.path.exists(temp_file_path):
                    file_size = os.path.getsize(temp_file_path)
            except:
                pass
            
            # Download the document
            if not self.blob_monitor.download_blob(document_name, temp_file_path):
                error_msg = f"Failed to download {document_name}"
                self.logger.error(error_msg)
                self.failed_tracker.add_failed_conversion(
                    filename=document_name,
                    error_type="DOWNLOAD_FAILED",
                    error_message=error_msg,
                    file_size_bytes=file_size
                )
                return
            
            # Convert the document
            converted_file_path = self.document_converter.convert_to_pdf(temp_file_path)
            
            if converted_file_path:
                # Upload the converted PDF
                pdf_blob_name = f"converted/{os.path.basename(converted_file_path)}"
                if self.blob_monitor.upload_blob(converted_file_path, pdf_blob_name):
                    self.logger.info(f"Successfully converted and uploaded: {document_name}")
                    # Mark as processed
                    self.blob_monitor.processed_files.add(document_name)
                else:
                    error_msg = f"Failed to upload converted PDF for {document_name}"
                    self.logger.error(error_msg)
                    self.failed_tracker.add_failed_conversion(
                        filename=document_name,
                        error_type="UPLOAD_FAILED",
                        error_message=error_msg,
                        file_size_bytes=file_size
                    )
            else:
                error_msg = f"Failed to convert {document_name}"
                self.logger.error(error_msg)
                self.failed_tracker.add_failed_conversion(
                    filename=document_name,
                    error_type="CONVERSION_FAILED",
                    error_message=error_msg,
                    file_size_bytes=file_size
                )
            
            # Clean up temporary files immediately after successful conversion
            if converted_file_path:
                # Delete the downloaded original file to conserve space
                self.document_converter.cleanup_temp_files(temp_file_path)
                self.logger.info(f"Deleted downloaded file to conserve space: {document_name}")
                
                # Also clean up the converted PDF from local storage after upload
                if os.path.exists(converted_file_path):
                    self.document_converter.cleanup_temp_files(converted_file_path)
                    self.logger.info(f"Cleaned up local PDF file: {os.path.basename(converted_file_path)}")
            else:
                # If conversion failed, still clean up the downloaded file
                self.document_converter.cleanup_temp_files(temp_file_path)
                self.logger.info(f"Cleaned up downloaded file after failed conversion: {document_name}")
                
        except Exception as e:
            error_msg = f"Error processing document {document_name}: {str(e)}"
            self.logger.error(error_msg)
            self.failed_tracker.add_failed_conversion(
                filename=document_name,
                error_type="PROCESSING_ERROR",
                error_message=error_msg,
                file_size_bytes=0
            )
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting Document Converter Application")
        self.logger.info(f"Monitoring for trigger file: {TRIGGER_FILE_PATTERN}")
        self.logger.info(f"Polling interval: {POLLING_INTERVAL} seconds")
        
        try:
            while True:
                # Check for trigger file
                if self.blob_monitor.check_for_trigger_file():
                    self.logger.info("Trigger file detected! Starting document conversion...")
                    self.process_documents()
                else:
                    self.logger.debug("No trigger file found, continuing to monitor...")
                
                # Wait before next check
                time.sleep(POLLING_INTERVAL)
                
        except KeyboardInterrupt:
            self.logger.info("Application stopped by user.")
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")

def main():
    """Main entry point."""
    app = DocumentConverterApp()
    app.run()

if __name__ == "__main__":
    main() 