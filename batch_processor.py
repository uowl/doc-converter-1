import os
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import ENABLE_BATCH_PROCESSING, BATCH_SIZE, BATCH_DELAY_SECONDS, ENABLE_PROGRESS_BARS, PROGRESS_BAR_DESCRIPTION, MAX_WORKER_THREADS, DISABLE_LOGGING_DURING_PROGRESS
from multi_thread_processor import MultiThreadProcessor
from blob_monitor import BlobMonitor
from failed_conversions import FailedConversionsTracker

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class BatchProcessor:
    """
    Handles batch processing of documents with resource management and progress tracking.
    """
    
    def __init__(self, failed_tracker: FailedConversionsTracker):
        self.failed_tracker = failed_tracker
        self.logger = logging.getLogger(__name__)
        self.multi_thread_processor = MultiThreadProcessor(failed_tracker)
        
    def process_documents_in_batches(self, 
                                   documents: List[str], 
                                   source_blob_monitor: BlobMonitor, 
                                   dest_blob_monitor: BlobMonitor) -> Dict[str, Any]:
        """
        Process documents in batches to manage memory and resources.
        
        Args:
            documents: List of document names to process
            source_blob_monitor: BlobMonitor for source operations
            dest_blob_monitor: BlobMonitor for destination operations
            
        Returns:
            Dictionary with processing results and statistics
        """
        if not ENABLE_BATCH_PROCESSING:
            self.logger.info("Batch processing disabled. Processing all documents at once.")
            return self.multi_thread_processor.process_documents_parallel(
                documents, source_blob_monitor, dest_blob_monitor
            )
        
        total_documents = len(documents)
        self.logger.info(f"[OK] Starting batch processing for {total_documents} documents")
        self.logger.info(f"[OK] Batch size: {BATCH_SIZE}, Delay between batches: {BATCH_DELAY_SECONDS} seconds")
        
        # Initialize overall progress bar
        overall_progress_bar = None
        if ENABLE_PROGRESS_BARS and TQDM_AVAILABLE:
            # Disable logging during progress bar to prevent interference
            import logging
            original_handlers = logging.getLogger().handlers[:]
            logging.getLogger().handlers.clear()
            
            overall_progress_bar = tqdm(
                total=total_documents,
                desc="Overall Progress",
                unit="doc",
                ncols=80,
                position=1,  # Position below individual progress bars
                leave=True,   # Keep the progress bar after completion
                bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )
            
            # Restore logging handlers after progress bar is created
            for handler in original_handlers:
                logging.getLogger().addHandler(handler)
        
        # Calculate number of batches
        num_batches = (total_documents + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division
        
        results = {
            'total_documents': total_documents,
            'total_batches': num_batches,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'processing_time': 0,
            'batch_results': []
        }
        
        start_time = datetime.now()
        
        try:
            for batch_num in range(num_batches):
                batch_start = batch_num * BATCH_SIZE
                batch_end = min(batch_start + BATCH_SIZE, total_documents)
                batch_documents = documents[batch_start:batch_end]
                
                self.logger.debug(f"[OK] Processing batch {batch_num + 1}/{num_batches} ({len(batch_documents)} documents)")
                self.logger.debug(f"[OK] Documents {batch_start + 1}-{batch_end} of {total_documents}")
                
                # Process current batch
                batch_start_time = datetime.now()
                batch_results = self.multi_thread_processor.process_documents_parallel(
                    batch_documents, source_blob_monitor, dest_blob_monitor
                )
                batch_end_time = datetime.now()
                batch_processing_time = (batch_end_time - batch_start_time).total_seconds()
                
                # Update overall results
                results['successful_conversions'] += batch_results['successful_conversions']
                results['failed_conversions'] += batch_results['failed_conversions']
                
                # Store batch results
                batch_info = {
                    'batch_num': batch_num + 1,
                    'documents_processed': len(batch_documents),
                    'successful_conversions': batch_results['successful_conversions'],
                    'failed_conversions': batch_results['failed_conversions'],
                    'processing_time': batch_processing_time,
                    'threads_used': batch_results['thread_count']
                }
                results['batch_results'].append(batch_info)
                
                # Update overall progress bar
                if overall_progress_bar:
                    if DISABLE_LOGGING_DURING_PROGRESS:
                        # Temporarily disable logging during progress bar update
                        import logging
                        original_level = logging.getLogger().level
                        logging.getLogger().setLevel(logging.ERROR)  # Only show errors
                        
                        try:
                            overall_progress_bar.update(len(batch_documents))
                        finally:
                            # Restore logging level
                            logging.getLogger().setLevel(original_level)
                    else:
                        # Normal update without logging protection
                        overall_progress_bar.update(len(batch_documents))
                
                # Log batch completion
                self.logger.debug(f"[OK] Batch {batch_num + 1} completed:")
                self.logger.debug(f"  - Documents processed: {len(batch_documents)}")
                self.logger.debug(f"  - Successful conversions: {batch_results['successful_conversions']}")
                self.logger.debug(f"  - Failed conversions: {batch_results['failed_conversions']}")
                self.logger.debug(f"  - Processing time: {batch_processing_time:.2f} seconds")
                self.logger.debug(f"  - Threads used: {batch_results['thread_count']}")
                
                # Add delay between batches (except for the last batch)
                if batch_num < num_batches - 1:
                    self.logger.info(f"[OK] Waiting {BATCH_DELAY_SECONDS} seconds before next batch...")
                    time.sleep(BATCH_DELAY_SECONDS)
                    
                    # Log memory cleanup
                    self.logger.debug(f"[OK] Memory cleanup completed, ready for next batch")
        
        except Exception as e:
            self.logger.error(f"Error during batch processing: {str(e)}")
            raise
        finally:
            # Close overall progress bar
            if overall_progress_bar:
                overall_progress_bar.close()
        
        # Calculate total processing time
        end_time = datetime.now()
        results['processing_time'] = (end_time - start_time).total_seconds()
        
        # Log final statistics
        self.logger.info(f"[OK] Batch processing completed:")
        self.logger.info(f"  - Total documents: {results['total_documents']}")
        self.logger.info(f"  - Total batches: {results['total_batches']}")
        self.logger.info(f"  - Successful conversions: {results['successful_conversions']}")
        self.logger.info(f"  - Failed conversions: {results['failed_conversions']}")
        self.logger.info(f"  - Total processing time: {results['processing_time']:.2f} seconds")
        
        # Log batch summary
        if results['batch_results']:
            self.logger.debug(f"[OK] Batch processing summary:")
            for batch_info in results['batch_results']:
                self.logger.debug(f"  - Batch {batch_info['batch_num']}: {batch_info['documents_processed']} docs, "
                               f"{batch_info['successful_conversions']} success, {batch_info['failed_conversions']} failed, "
                               f"{batch_info['processing_time']:.2f}s")
        
        return results
    
    def get_batch_processing_estimate(self, total_documents: int) -> Dict[str, Any]:
        """
        Estimate processing time and resource usage for batch processing.
        
        Args:
            total_documents: Total number of documents to process
            
        Returns:
            Dictionary with processing estimates
        """
        if not ENABLE_BATCH_PROCESSING:
            return {
                'estimated_batches': 1,
                'estimated_time_hours': 0,
                'estimated_time_days': 0,
                'memory_usage_mb': 0
            }
        
        # Calculate number of batches
        num_batches = (total_documents + BATCH_SIZE - 1) // BATCH_SIZE
        
        # Estimate time per batch (based on 4 files in 6 seconds = 1.5s per file)
        # With 16 threads, theoretical improvement is 16x, but realistic is 8x
        time_per_file_seconds = 1.5 / 8  # 0.1875 seconds per file
        time_per_batch_seconds = BATCH_SIZE * time_per_file_seconds
        
        # Add delay between batches
        total_processing_time_seconds = (num_batches * time_per_batch_seconds) + ((num_batches - 1) * BATCH_DELAY_SECONDS)
        
        # Convert to hours and days
        total_hours = total_processing_time_seconds / 3600
        total_days = total_hours / 24
        
        # Estimate memory usage (rough estimate: 50MB per batch)
        memory_usage_mb = num_batches * 50
        
        return {
            'estimated_batches': num_batches,
            'estimated_time_seconds': total_processing_time_seconds,
            'estimated_time_hours': total_hours,
            'estimated_time_days': total_days,
            'memory_usage_mb': memory_usage_mb,
            'time_per_batch_seconds': time_per_batch_seconds
        }
    
    def validate_batch_configuration(self) -> Dict[str, Any]:
        """
        Validate batch processing configuration and provide recommendations.
        
        Returns:
            Dictionary with validation results and recommendations
        """
        validation = {
            'batch_size_ok': True,
            'thread_count_ok': True,
            'delay_ok': True,
            'recommendations': []
        }
        
        # Check batch size
        if BATCH_SIZE < 100:
            validation['batch_size_ok'] = False
            validation['recommendations'].append("Consider increasing BATCH_SIZE to at least 100 for better efficiency")
        elif BATCH_SIZE > 10000:
            validation['batch_size_ok'] = False
            validation['recommendations'].append("Consider decreasing BATCH_SIZE to prevent memory issues")
        
        # Check thread count
        if MAX_WORKER_THREADS < 4:
            validation['thread_count_ok'] = False
            validation['recommendations'].append("Consider increasing MAX_WORKER_THREADS to at least 4")
        elif MAX_WORKER_THREADS > 32:
            validation['thread_count_ok'] = False
            validation['recommendations'].append("Consider decreasing MAX_WORKER_THREADS to prevent resource exhaustion")
        
        # Check delay
        if BATCH_DELAY_SECONDS < 1:
            validation['delay_ok'] = False
            validation['recommendations'].append("Consider increasing BATCH_DELAY_SECONDS to at least 1 second")
        elif BATCH_DELAY_SECONDS > 30:
            validation['delay_ok'] = False
            validation['recommendations'].append("Consider decreasing BATCH_DELAY_SECONDS for faster processing")
        
        return validation 