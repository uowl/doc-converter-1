import os
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import ENABLE_MULTI_THREADING, MAX_WORKER_THREADS, MIN_FILES_FOR_MULTI_THREADING, ENABLE_PROGRESS_BARS, PROGRESS_BAR_DESCRIPTION
from blob_monitor import BlobMonitor
from document_converter import DocumentConverter
from failed_conversions import FailedConversionsTracker

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class MultiThreadProcessor:
    """
    Handles multi-threaded document processing with thread-safe operations.
    """
    
    def __init__(self, failed_tracker: FailedConversionsTracker):
        self.failed_tracker = failed_tracker
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()  # Thread lock for shared resources
        self._progress_lock = threading.Lock()  # Lock for progress bar updates
        
    def process_documents_parallel(self, 
                                 documents: List[str], 
                                 source_blob_monitor: BlobMonitor, 
                                 dest_blob_monitor: BlobMonitor) -> Dict[str, Any]:
        """
        Process documents in parallel using multiple threads.
        
        Args:
            documents: List of document names to process
            source_blob_monitor: BlobMonitor for source operations
            dest_blob_monitor: BlobMonitor for destination operations
            
        Returns:
            Dictionary with processing results and statistics
        """
        if not ENABLE_MULTI_THREADING or len(documents) < MIN_FILES_FOR_MULTI_THREADING:
            self.logger.info(f"Multi-threading disabled or insufficient files ({len(documents)} < {MIN_FILES_FOR_MULTI_THREADING}). Using single-threaded processing.")
            return self._process_documents_sequential(documents, source_blob_monitor, dest_blob_monitor)
        
        self.logger.info(f"[OK] Starting multi-threaded processing with {MAX_WORKER_THREADS} threads for {len(documents)} documents")
        
        results = {
            'total_documents': len(documents),
            'successful_conversions': 0,
            'failed_conversions': 0,
            'processing_time': 0,
            'thread_count': min(MAX_WORKER_THREADS, len(documents))
        }
        
        start_time = datetime.now()
        
        # Initialize progress bar if enabled
        progress_bar = None
        if ENABLE_PROGRESS_BARS and TQDM_AVAILABLE:
            progress_bar = tqdm(
                total=len(documents),
                desc=PROGRESS_BAR_DESCRIPTION,
                unit="doc",
                ncols=80,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )
        
        # Create thread-local storage for document converters
        thread_local = threading.local()
        

        
        def get_thread_converter():
            """Get or create a document converter for the current thread."""
            if not hasattr(thread_local, 'converter'):
                thread_local.converter = DocumentConverter()
            return thread_local.converter
        
        def process_single_document_thread_safe(document_name: str) -> Dict[str, Any]:
            """
            Process a single document with thread-safe operations.
            
            Args:
                document_name: Name of the document to process
                
            Returns:
                Dictionary with processing result
            """
            thread_id = threading.current_thread().ident
            filename = os.path.basename(document_name)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Update progress bar description with current file
            if progress_bar:
                with self._progress_lock:
                    progress_bar.set_description(f"Converting {filename}")
            
            result = {
                'document_name': document_name,
                'filename': filename,
                'thread_id': thread_id,
                'success': False,
                'error_type': None,
                'error_message': None,
                'file_size': 0
            }
            
            try:
                # Thread-safe logging
                with self._lock:
                    self.logger.debug(f"[Thread-{thread_id}] Processing document: {filename}")
                
                # Create temporary file path with thread-specific naming to avoid conflicts
                temp_file_path = os.path.join("temp", f"thread_{thread_id}_{filename}")
                os.makedirs("temp", exist_ok=True)
                
                # Get file size for tracking
                try:
                    if os.path.exists(temp_file_path):
                        result['file_size'] = os.path.getsize(temp_file_path)
                except:
                    pass
                
                # Download the document from source
                if not source_blob_monitor.download_blob(document_name, temp_file_path):
                    error_msg = f"[FAILED] Failed to download {filename} from source"
                    with self._lock:
                        self.logger.error(f"[Thread-{thread_id}] {error_msg}")
                    result['error_type'] = "DOWNLOAD_FAILED"
                    result['error_message'] = error_msg
                    return result
                
                # Get thread-local document converter
                document_converter = get_thread_converter()
                
                # Process the document based on file type
                if file_ext in ['.pdf', '.tif', '.tiff']:
                    # For PDF and TIF files, copy as-is
                    converted_file_path = document_converter.convert_to_pdf(temp_file_path)
                    if converted_file_path:
                        file_type = "PDF" if file_ext == '.pdf' else "TIF"
                        with self._lock:
                            self.logger.debug(f"[Thread-{thread_id}] [OK] Successfully copied {file_type} file: {filename}")
                    else:
                        file_type = "PDF" if file_ext == '.pdf' else "TIF"
                        error_msg = f"[FAILED] Failed to copy {file_type} file {filename}"
                        with self._lock:
                            self.logger.error(f"[Thread-{thread_id}] {error_msg}")
                        result['error_type'] = "COPY_FAILED"
                        result['error_message'] = error_msg
                        return result
                else:
                    # For other files, convert to PDF
                    converted_file_path = document_converter.convert_to_pdf(temp_file_path)
                    if not converted_file_path:
                        error_msg = f"[FAILED] Failed to convert {filename}"
                        with self._lock:
                            self.logger.error(f"[Thread-{thread_id}] {error_msg}")
                        result['error_type'] = "CONVERSION_FAILED"
                        result['error_message'] = error_msg
                        return result
                
                # Upload the processed file to destination
                if converted_file_path:
                    # Get the original filename without thread information
                    original_filename = os.path.basename(document_name)
                    original_base_name = os.path.splitext(original_filename)[0]
                    
                    # For TIF files, keep original extension; for others, use PDF extension
                    if file_ext in ['.tif', '.tiff']:
                        dest_filename = original_filename  # Keep original filename with extension
                    else:
                        dest_filename = f"{original_base_name}.pdf"  # Use PDF extension for converted files
                    
                    blob_name = f"converted/{dest_filename}"
                    
                    # If destination has additional path, prepend it to the blob name
                    if hasattr(dest_blob_monitor, 'additional_path') and dest_blob_monitor.additional_path:
                        blob_name = f"{dest_blob_monitor.additional_path}/{blob_name}"
                    
                    if dest_blob_monitor.upload_blob(converted_file_path, blob_name):
                        if file_ext in ['.pdf', '.tif', '.tiff']:
                            file_type = "PDF" if file_ext == '.pdf' else "TIF"
                            with self._lock:
                                self.logger.debug(f"[Thread-{thread_id}] [OK] Successfully copied and uploaded {file_type}: {filename}")
                        else:
                            with self._lock:
                                self.logger.debug(f"[Thread-{thread_id}] [OK] Successfully converted and uploaded: {filename}")
                        
                        # Mark as processed (thread-safe)
                        with self._lock:
                            source_blob_monitor.processed_files.add(document_name)
                        
                        result['success'] = True
                    else:
                        error_msg = f"[FAILED] Failed to upload processed file for {filename} to destination"
                        with self._lock:
                            self.logger.error(f"[Thread-{thread_id}] {error_msg}")
                        result['error_type'] = "UPLOAD_FAILED"
                        result['error_message'] = error_msg
                        return result
                
                # Clean up temporary files immediately after successful processing
                if converted_file_path:
                    # Delete the downloaded original file to conserve space
                    document_converter.cleanup_temp_files(temp_file_path)
                    if file_ext in ['.pdf', '.tif', '.tiff']:
                        file_type = "PDF" if file_ext == '.pdf' else "TIF"
                        with self._lock:
                            self.logger.debug(f"[Thread-{thread_id}] Deleted downloaded {file_type} file to conserve space: {filename}")
                    else:
                        with self._lock:
                            self.logger.debug(f"[Thread-{thread_id}] Deleted downloaded file to conserve space: {filename}")
                    
                    # Also clean up the processed file from local storage after upload
                    if os.path.exists(converted_file_path):
                        document_converter.cleanup_temp_files(converted_file_path)
                        with self._lock:
                            self.logger.debug(f"[Thread-{thread_id}] Cleaned up local processed file: {os.path.basename(converted_file_path)}")
                else:
                    # If processing failed, still clean up the downloaded file
                    document_converter.cleanup_temp_files(temp_file_path)
                    with self._lock:
                        self.logger.debug(f"[Thread-{thread_id}] Cleaned up downloaded file after failed processing: {filename}")
                
            except Exception as e:
                error_msg = f"Error processing document {filename}: {str(e)}"
                with self._lock:
                    self.logger.error(f"[Thread-{thread_id}] {error_msg}")
                result['error_type'] = "PROCESSING_ERROR"
                result['error_message'] = error_msg
            
            return result
        
        # Process documents using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=MAX_WORKER_THREADS) as executor:
            # Submit all tasks
            future_to_document = {
                executor.submit(process_single_document_thread_safe, doc): doc 
                for doc in documents
            }
            
            # Process completed tasks
            for future in as_completed(future_to_document):
                document_name = future_to_document[future]
                try:
                    result = future.result()
                    
                    # Thread-safe result processing
                    with self._lock:
                        if result['success']:
                            results['successful_conversions'] += 1
                        else:
                            results['failed_conversions'] += 1
                            # Add to failed conversions tracker
                            self.failed_tracker.add_failed_conversion(
                                filename=result['filename'],
                                error_type=result['error_type'],
                                error_message=result['error_message'],
                                file_size_bytes=result['file_size']
                            )
                    
                    # Update progress bar
                    if progress_bar:
                        with self._progress_lock:
                            progress_bar.update(1)
                            
                except Exception as e:
                    with self._lock:
                        self.logger.error(f"Exception in thread processing {document_name}: {str(e)}")
                        results['failed_conversions'] += 1
                    
                    # Update progress bar even for exceptions
                    if progress_bar:
                        with self._progress_lock:
                            progress_bar.update(1)
        
        # Close progress bar
        if progress_bar:
            progress_bar.close()
        
        # Calculate processing time
        end_time = datetime.now()
        results['processing_time'] = (end_time - start_time).total_seconds()
        
        # Log final statistics
        self.logger.info(f"[OK] Multi-threaded processing completed:")
        self.logger.info(f"  - Total documents: {results['total_documents']}")
        self.logger.info(f"  - Successful conversions: {results['successful_conversions']}")
        self.logger.info(f"  - Failed conversions: {results['failed_conversions']}")
        self.logger.info(f"  - Processing time: {results['processing_time']:.2f} seconds")
        self.logger.info(f"  - Threads used: {results['thread_count']}")
        
        return results
    
    def _process_documents_sequential(self, 
                                    documents: List[str], 
                                    source_blob_monitor: BlobMonitor, 
                                    dest_blob_monitor: BlobMonitor) -> Dict[str, Any]:
        """
        Process documents sequentially (fallback for single-threaded processing).
        
        Args:
            documents: List of document names to process
            source_blob_monitor: BlobMonitor for source operations
            dest_blob_monitor: BlobMonitor for destination operations
            
        Returns:
            Dictionary with processing results and statistics
        """
        self.logger.info(f"Processing {len(documents)} documents sequentially")
        
        results = {
            'total_documents': len(documents),
            'successful_conversions': 0,
            'failed_conversions': 0,
            'processing_time': 0,
            'thread_count': 1
        }
        
        start_time = datetime.now()
        
        # Initialize progress bar for sequential processing
        progress_bar = None
        if ENABLE_PROGRESS_BARS and TQDM_AVAILABLE:
            progress_bar = tqdm(
                total=len(documents),
                desc=PROGRESS_BAR_DESCRIPTION,
                unit="doc",
                ncols=80,
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
            )
        
        document_converter = DocumentConverter()
        
        for document_name in documents:
            filename = os.path.basename(document_name)
            file_ext = os.path.splitext(filename)[1].lower()
            self.logger.debug(f"Processing document: {filename}")
            
            # Update progress bar description
            if progress_bar:
                progress_bar.set_description(f"Converting {filename}")
            
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
            
            try:
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
                    results['failed_conversions'] += 1
                    continue
                
                # Process the document based on file type
                if file_ext in ['.pdf', '.tif', '.tiff']:
                    # For PDF and TIF files, copy as-is
                    converted_file_path = document_converter.convert_to_pdf(temp_file_path)
                    if converted_file_path:
                        file_type = "PDF" if file_ext == '.pdf' else "TIF"
                        self.logger.debug(f"[OK] Successfully copied {file_type} file: {filename}")
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
                        results['failed_conversions'] += 1
                        continue
                else:
                    # For other files, convert to PDF
                    converted_file_path = document_converter.convert_to_pdf(temp_file_path)
                    if not converted_file_path:
                        error_msg = f"[FAILED] Failed to convert {filename}"
                        self.logger.error(error_msg)
                        self.failed_tracker.add_failed_conversion(
                            filename=filename,
                            error_type="CONVERSION_FAILED",
                            error_message=error_msg,
                            file_size_bytes=file_size
                        )
                        results['failed_conversions'] += 1
                        continue
                
                # Upload the processed file to destination
                if converted_file_path:
                    # Get the original filename without thread information
                    original_filename = os.path.basename(document_name)
                    original_base_name = os.path.splitext(original_filename)[0]
                    
                    # For TIF files, keep original extension; for others, use PDF extension
                    if file_ext in ['.tif', '.tiff']:
                        dest_filename = original_filename  # Keep original filename with extension
                    else:
                        dest_filename = f"{original_base_name}.pdf"  # Use PDF extension for converted files
                    
                    blob_name = f"converted/{dest_filename}"
                    
                    # If destination has additional path, prepend it to the blob name
                    if hasattr(dest_blob_monitor, 'additional_path') and dest_blob_monitor.additional_path:
                        blob_name = f"{dest_blob_monitor.additional_path}/{blob_name}"
                    
                    if dest_blob_monitor.upload_blob(converted_file_path, blob_name):
                        if file_ext in ['.pdf', '.tif', '.tiff']:
                            file_type = "PDF" if file_ext == '.pdf' else "TIF"
                            self.logger.debug(f"[OK] Successfully copied and uploaded {file_type}: {filename}")
                        else:
                            self.logger.debug(f"[OK] Successfully converted and uploaded: {filename}")
                        # Mark as processed
                        source_blob_monitor.processed_files.add(document_name)
                        results['successful_conversions'] += 1
                    else:
                        error_msg = f"[FAILED] Failed to upload processed file for {filename} to destination"
                        self.logger.error(error_msg)
                        self.failed_tracker.add_failed_conversion(
                            filename=filename,
                            error_type="UPLOAD_FAILED",
                            error_message=error_msg,
                            file_size_bytes=file_size
                        )
                        results['failed_conversions'] += 1
                
                # Clean up temporary files immediately after successful processing
                if converted_file_path:
                    # Delete the downloaded original file to conserve space
                    document_converter.cleanup_temp_files(temp_file_path)
                    if file_ext in ['.pdf', '.tif', '.tiff']:
                        file_type = "PDF" if file_ext == '.pdf' else "TIF"
                        self.logger.debug(f"Deleted downloaded {file_type} file to conserve space: {filename}")
                    else:
                        self.logger.debug(f"Deleted downloaded file to conserve space: {filename}")
                    
                    # Also clean up the processed file from local storage after upload
                    if os.path.exists(converted_file_path):
                        document_converter.cleanup_temp_files(converted_file_path)
                        self.logger.debug(f"Cleaned up local processed file: {os.path.basename(converted_file_path)}")
                else:
                    # If processing failed, still clean up the downloaded file
                    document_converter.cleanup_temp_files(temp_file_path)
                    self.logger.debug(f"Cleaned up downloaded file after failed processing: {filename}")
                    
            except Exception as e:
                error_msg = f"Error processing document {filename}: {str(e)}"
                self.logger.error(error_msg)
                self.failed_tracker.add_failed_conversion(
                    filename=filename,
                    error_type="PROCESSING_ERROR",
                    error_message=error_msg,
                    file_size_bytes=0
                )
                results['failed_conversions'] += 1
            
            # Update progress bar for each document processed
            if progress_bar:
                progress_bar.update(1)
        
        # Close progress bar
        if progress_bar:
            progress_bar.close()
        
        # Calculate processing time
        end_time = datetime.now()
        results['processing_time'] = (end_time - start_time).total_seconds()
        
        # Log final statistics
        self.logger.info(f"[OK] Sequential processing completed:")
        self.logger.info(f"  - Total documents: {results['total_documents']}")
        self.logger.info(f"  - Successful conversions: {results['successful_conversions']}")
        self.logger.info(f"  - Failed conversions: {results['failed_conversions']}")
        self.logger.info(f"  - Processing time: {results['processing_time']:.2f} seconds")
        
        return results 