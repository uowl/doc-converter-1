import time
import os
import logging
from datetime import datetime, timedelta
from blob_monitor import BlobMonitor
from document_converter import DocumentConverter
from failed_conversions import FailedConversionsTracker
from multi_thread_processor import MultiThreadProcessor
from batch_processor import BatchProcessor
from config import POLLING_INTERVAL, TRIGGER_FILE_PATTERN, AZURE_CONFIG_FOLDER, AZURE_FILES_FOLDER, ENABLE_MULTI_THREADING, MAX_WORKER_THREADS, MIN_FILES_FOR_MULTI_THREADING, ENABLE_PROGRESS_BARS, ENABLE_BATCH_PROCESSING, BATCH_SIZE, BATCH_DELAY_SECONDS, LOG_LEVEL, PROGRESS_BAR_LOG_DELAY

class DocumentConverterApp:
    def __init__(self):
        # Initialize with main SAS URL for monitoring trigger files
        self.main_blob_monitor = BlobMonitor()
        self.document_converter = DocumentConverter()
        self.failed_tracker = FailedConversionsTracker()
        self.multi_thread_processor = MultiThreadProcessor(self.failed_tracker)
        self.batch_processor = BatchProcessor(self.failed_tracker)
        self.logger = logging.getLogger(__name__)
        
        # Setup logging with reduced Azure SDK verbosity
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
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
                self.logger.debug(f"[OK] Uploaded job log to {dest_blob_path} in main SAS URL container.")
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
            
            self.logger.debug(f"Using source SAS URL: {source_sas_url}")
            self.logger.debug(f"Using destination SAS URL: {dest_sas_url}")
            
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
            
            # Small delay to prevent progress bar interference
            import time
            time.sleep(PROGRESS_BAR_LOG_DELAY)
            
            # Log multi-threading configuration
            if ENABLE_MULTI_THREADING:
                self.logger.debug(f"[OK] Multi-threading enabled with {MAX_WORKER_THREADS} max threads")
                self.logger.debug(f"[OK] Minimum files for multi-threading: {MIN_FILES_FOR_MULTI_THREADING}")
            else:
                self.logger.info("[OK] Multi-threading disabled - using sequential processing")
            
            # Log progress bar configuration
            if ENABLE_PROGRESS_BARS:
                self.logger.debug("[OK] Progress bars enabled - will show conversion progress")
            else:
                self.logger.debug("[OK] Progress bars disabled - using standard logging only")
            
            # Log batch processing configuration
            if ENABLE_BATCH_PROCESSING:
                self.logger.info(f"[OK] Batch processing enabled - batch size: {BATCH_SIZE}, delay: {BATCH_DELAY_SECONDS}s")
                
                # Get processing estimates
                estimates = self.batch_processor.get_batch_processing_estimate(len(documents))
                self.logger.info(f"[OK] Processing estimates:")
                self.logger.info(f"  - Estimated batches: {estimates['estimated_batches']}")
                self.logger.info(f"  - Estimated time: {estimates['estimated_time_hours']:.1f} hours ({estimates['estimated_time_days']:.1f} days)")
                self.logger.info(f"  - Estimated memory usage: {estimates['memory_usage_mb']:.0f} MB")
                
                # Validate batch configuration
                validation = self.batch_processor.validate_batch_configuration()
                if not all([validation['batch_size_ok'], validation['thread_count_ok'], validation['delay_ok']]):
                    self.logger.warning("[WARNING] Batch configuration issues detected:")
                    for recommendation in validation['recommendations']:
                        self.logger.warning(f"  - {recommendation}")
            else:
                self.logger.info("[OK] Batch processing disabled - processing all documents at once")
            
            # Process documents using batch processor
            processing_results = self.batch_processor.process_documents_in_batches(
                documents, source_blob_monitor, dest_blob_monitor
            )
            
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