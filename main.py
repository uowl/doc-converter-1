import time
import os
import logging
from datetime import datetime, timedelta
from blob_monitor import BlobMonitor
from document_converter import DocumentConverter
from failed_conversions import FailedConversionsTracker
from config import POLLING_INTERVAL, TRIGGER_FILE_PATTERN, AZURE_CONFIG_FOLDER, AZURE_FILES_FOLDER

class DocumentConverterApp:
    def __init__(self):
        # Initialize with main SAS URL for monitoring trigger files
        self.main_blob_monitor = BlobMonitor()
        self.document_converter = DocumentConverter()
        self.failed_tracker = FailedConversionsTracker()
        self.logger = logging.getLogger(__name__)
        
        # Setup logging with reduced Azure SDK verbosity
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('doc_converter.log'),
                logging.StreamHandler()
            ]
        )
        
        # Reduce Azure SDK logging verbosity based on configuration
        from config import VERBOSE_AZURE_LOGS
        if not VERBOSE_AZURE_LOGS:
            logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
            logging.getLogger('azure.storage.blob').setLevel(logging.WARNING)
            logging.getLogger('azure.core.pipeline').setLevel(logging.WARNING)
            logging.getLogger('azure.core.pipeline.transport').setLevel(logging.WARNING)
    
    def _print_next_polling_time(self):
        """Print the time when the next polling will occur."""
        next_polling_time = datetime.now() + timedelta(seconds=POLLING_INTERVAL)
        self.logger.info(f"Next polling will occur at: {next_polling_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _upload_job_log(self):
        """Upload the doc_converter.log file to the main SAS URL's job_status/ folder with a datetime-stamped filename."""
        try:
            from config import LOG_FILE
            log_file = LOG_FILE
            if not os.path.exists(log_file):
                self.logger.warning(f"Log file {log_file} does not exist, skipping upload.")
                return
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_blob_path = f"job_status/job_{timestamp}.log"
            success = self.main_blob_monitor.upload_local_file(log_file, dest_blob_path)
            if success:
                self.logger.info(f"[OK] Uploaded job log to {dest_blob_path} in main SAS URL container.")
            else:
                self.logger.error(f"[FAILED] Failed to upload job log to {dest_blob_path}.")
        except Exception as e:
            self.logger.error(f"Error uploading job log: {str(e)}")
    
    def process_documents(self):
        """Process all documents when trigger file is found."""
        try:
            self.logger.info("Starting document processing...")
            
            # Get trigger file configuration with source and destination SAS URLs
            trigger_config = self.main_blob_monitor.get_trigger_file_config()
            source_sas_url = trigger_config['source_sas_url']
            dest_sas_url = trigger_config['dest_sas_url']
            
            self.logger.info(f"Using source SAS URL: {source_sas_url}")
            self.logger.info(f"Using destination SAS URL: {dest_sas_url}")
            
            # Create source and destination blob monitors
            source_blob_monitor = BlobMonitor(source_sas_url)
            dest_blob_monitor = BlobMonitor(dest_sas_url)
            
            # Get list of documents to convert from source
            documents = source_blob_monitor.get_documents_to_convert()
            
            if not documents:
                self.logger.info("No documents found to convert in source Azure files folder.")
                self._upload_job_log()
                return
            
            self.logger.info(f"Found {len(documents)} documents to convert from source Azure files folder.")
            
            # Process each document
            for document_name in documents:
                self._process_single_document(document_name, source_blob_monitor, dest_blob_monitor)
            
            # Delete the trigger file after processing
            self.main_blob_monitor.delete_trigger_file()
            
            # Display failure summary after processing
            self._display_failure_summary()
            
            self.logger.info("Document processing completed.")
            
            # Print next polling time after processing is completed
            self._print_next_polling_time()
            
        except Exception as e:
            self.logger.error(f"Error in document processing: {str(e)}")
        finally:
            self._upload_job_log()
    
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
                self.logger.info("[OK] No failed conversions recorded")
                
        except Exception as e:
            self.logger.error(f"Error displaying failure summary: {str(e)}")
    
    def _process_single_document(self, document_name, source_blob_monitor, dest_blob_monitor):
        """Process a single document using source and destination blob monitors."""
        try:
            # Extract just the filename for display
            filename = os.path.basename(document_name)
            file_ext = os.path.splitext(filename)[1].lower()
            self.logger.info(f"Processing document: {filename} (from {document_name})")
            
            # Create temporary file path
            temp_file_path = os.path.join("temp", filename)
            os.makedirs("temp", exist_ok=True)
            
            # Get file size for tracking
            file_size = 0
            try:
                if os.path.exists(temp_file_path):
                    file_size = os.path.getsize(temp_file_path)
            except:
                pass
            
            # Download the document from source
            if not source_blob_monitor.download_blob(document_name, temp_file_path):
                error_msg = f"[FAILED] Failed to download {filename} from source"
                self.logger.error(error_msg)
                self.failed_tracker.add_failed_conversion(
                    filename=filename,
                    error_type="DOWNLOAD_FAILED",
                    error_message=error_msg,
                    file_size_bytes=file_size
                )
                return
            
            # Process the document based on file type
            if file_ext in ['.pdf', '.tif', '.tiff']:
                # For PDF and TIF files, copy as-is
                converted_file_path = self.document_converter.convert_to_pdf(temp_file_path)
                if converted_file_path:
                    file_type = "PDF" if file_ext == '.pdf' else "TIF"
                    self.logger.info(f"[OK] Successfully copied {file_type} file: {filename}")
                else:
                    file_type = "PDF" if file_ext == '.pdf' else "TIF"
                    error_msg = f"[FAILED] Failed to copy {file_type} file {filename}"
                    self.logger.error(error_msg)
                    self.failed_tracker.add_failed_conversion(
                        filename=filename,
                        error_type="COPY_FAILED",
                        error_message=error_msg,
                        file_size_bytes=file_size
                    )
                    return
            else:
                # For other files, convert to PDF
                converted_file_path = self.document_converter.convert_to_pdf(temp_file_path)
                if not converted_file_path:
                    error_msg = f"[FAILED] Failed to convert {filename}"
                    self.logger.error(error_msg)
                    self.failed_tracker.add_failed_conversion(
                        filename=filename,
                        error_type="CONVERSION_FAILED",
                        error_message=error_msg,
                        file_size_bytes=file_size
                    )
                    return
            
            # Upload the processed file to destination
            if converted_file_path:
                # Upload the processed file to the converted folder in destination
                processed_filename = os.path.basename(converted_file_path)
                # For TIF files, keep original extension; for others, use PDF extension
                if file_ext in ['.tif', '.tiff']:
                    blob_name = f"converted/{processed_filename}"  # Keep original TIF extension
                else:
                    blob_name = f"converted/{processed_filename}"  # Use PDF extension for converted files
                
                # If destination has additional path, prepend it to the blob name
                if hasattr(dest_blob_monitor, 'additional_path') and dest_blob_monitor.additional_path:
                    blob_name = f"{dest_blob_monitor.additional_path}/{blob_name}"
                
                if dest_blob_monitor.upload_blob(converted_file_path, blob_name):
                    if file_ext in ['.pdf', '.tif', '.tiff']:
                        file_type = "PDF" if file_ext == '.pdf' else "TIF"
                        self.logger.info(f"[OK] Successfully copied and uploaded {file_type}: {filename}")
                    else:
                        self.logger.info(f"[OK] Successfully converted and uploaded: {filename}")
                    # Mark as processed
                    source_blob_monitor.processed_files.add(document_name)
                else:
                    error_msg = f"[FAILED] Failed to upload processed file for {filename} to destination"
                    self.logger.error(error_msg)
                    self.failed_tracker.add_failed_conversion(
                        filename=filename,
                        error_type="UPLOAD_FAILED",
                        error_message=error_msg,
                        file_size_bytes=file_size
                    )
            
            # Clean up temporary files immediately after successful processing
            if converted_file_path:
                # Delete the downloaded original file to conserve space
                self.document_converter.cleanup_temp_files(temp_file_path)
                if file_ext in ['.pdf', '.tif', '.tiff']:
                    file_type = "PDF" if file_ext == '.pdf' else "TIF"
                    self.logger.info(f"Deleted downloaded {file_type} file to conserve space: {filename}")
                else:
                    self.logger.info(f"Deleted downloaded file to conserve space: {filename}")
                
                # Also clean up the processed file from local storage after upload
                if os.path.exists(converted_file_path):
                    self.document_converter.cleanup_temp_files(converted_file_path)
                    self.logger.info(f"Cleaned up local processed file: {os.path.basename(converted_file_path)}")
            else:
                # If processing failed, still clean up the downloaded file
                self.document_converter.cleanup_temp_files(temp_file_path)
                self.logger.info(f"Cleaned up downloaded file after failed processing: {filename}")
                
        except Exception as e:
            error_msg = f"Error processing document {filename}: {str(e)}"
            self.logger.error(error_msg)
            self.failed_tracker.add_failed_conversion(
                filename=filename,
                error_type="PROCESSING_ERROR",
                error_message=error_msg,
                file_size_bytes=0
            )
    
    def run(self):
        """Main application loop."""
        self.logger.info("Starting Document Converter Application")
        self.logger.info(f"Monitoring Azure config folder for trigger file: {AZURE_CONFIG_FOLDER}/{TRIGGER_FILE_PATTERN}")
        self.logger.info(f"Processing files from Azure files folder: {AZURE_FILES_FOLDER}/")
        self.logger.info(f"Polling interval: {POLLING_INTERVAL} seconds")
        
        try:
            while True:
                # Check for trigger file
                if self.main_blob_monitor.check_for_trigger_file():
                    self.logger.info("Trigger file detected! Starting document conversion...")
                    self.process_documents()
                else:
                    self.logger.debug("No trigger file found, continuing to monitor...")
                    # Print next polling time during regular polling cycle
                    self._print_next_polling_time()
                
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