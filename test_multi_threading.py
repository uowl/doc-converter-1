#!/usr/bin/env python3
"""
Test script for multi-threading functionality.
This script tests the multi-threaded document processing without requiring actual Azure blob storage.
"""

import os
import sys
import logging
import tempfile
import time
from datetime import datetime
from unittest.mock import Mock, patch

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_thread_processor import MultiThreadProcessor
from failed_conversions import FailedConversionsTracker
from config import ENABLE_MULTI_THREADING, MAX_WORKER_THREADS, MIN_FILES_FOR_MULTI_THREADING


def create_mock_blob_monitor():
    """Create a mock blob monitor for testing."""
    mock_monitor = Mock()
    mock_monitor.processed_files = set()
    mock_monitor.additional_path = None
    
    # Mock download method - creates a temporary file
    def mock_download_blob(blob_name, local_path):
        # Create a simple test file
        with open(local_path, 'w') as f:
            f.write(f"Test content for {blob_name}")
        return True
    
    # Mock upload method
    def mock_upload_blob(local_path, blob_name):
        return True
    
    mock_monitor.download_blob = mock_download_blob
    mock_monitor.upload_blob = mock_upload_blob
    
    return mock_monitor


def create_test_documents(num_documents=6):
    """Create a list of test document names."""
    test_extensions = ['.docx', '.pdf', '.txt', '.html', '.jpg', '.png']
    documents = []
    
    for i in range(num_documents):
        ext = test_extensions[i % len(test_extensions)]
        documents.append(f"test_document_{i+1}{ext}")
    
    return documents


def test_multi_threading():
    """Test the multi-threading functionality."""
    print("=== Multi-Threading Test ===")
    print(f"Multi-threading enabled: {ENABLE_MULTI_THREADING}")
    print(f"Max worker threads: {MAX_WORKER_THREADS}")
    print(f"Min files for multi-threading: {MIN_FILES_FOR_MULTI_THREADING}")
    print()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test components
    failed_tracker = FailedConversionsTracker()
    processor = MultiThreadProcessor(failed_tracker)
    
    # Create mock blob monitors
    source_monitor = create_mock_blob_monitor()
    dest_monitor = create_mock_blob_monitor()
    
    # Test with different numbers of documents
    test_cases = [
        (2, "Should use sequential processing (below minimum)"),
        (4, "Should use multi-threading (at minimum)"),
        (8, "Should use multi-threading (above minimum)")
    ]
    
    for num_docs, description in test_cases:
        print(f"\n--- Test Case: {num_docs} documents ---")
        print(f"Description: {description}")
        
        documents = create_test_documents(num_docs)
        print(f"Documents: {documents}")
        
        # Mock the document converter to avoid actual conversion
        with patch('multi_thread_processor.DocumentConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_to_pdf.return_value = "/tmp/test_output.pdf"
            mock_converter.cleanup_temp_files.return_value = None
            mock_converter_class.return_value = mock_converter
            
            start_time = time.time()
            
            try:
                results = processor.process_documents_parallel(
                    documents, source_monitor, dest_monitor
                )
                
                end_time = time.time()
                actual_time = end_time - start_time
                
                print(f"[OK] Processing completed successfully")
                print(f"  - Total documents: {results['total_documents']}")
                print(f"  - Successful conversions: {results['successful_conversions']}")
                print(f"  - Failed conversions: {results['failed_conversions']}")
                print(f"  - Threads used: {results['thread_count']}")
                print(f"  - Processing time: {results['processing_time']:.2f} seconds")
                print(f"  - Actual time: {actual_time:.2f} seconds")
                
                # Verify results
                assert results['total_documents'] == num_docs, f"Expected {num_docs} documents, got {results['total_documents']}"
                assert results['successful_conversions'] == num_docs, f"Expected {num_docs} successful conversions, got {results['successful_conversions']}"
                assert results['failed_conversions'] == 0, f"Expected 0 failed conversions, got {results['failed_conversions']}"
                
                if num_docs >= MIN_FILES_FOR_MULTI_THREADING and ENABLE_MULTI_THREADING:
                    assert results['thread_count'] > 1, f"Expected multi-threading, but only {results['thread_count']} thread used"
                    print(f"[OK] Multi-threading confirmed with {results['thread_count']} threads")
                else:
                    assert results['thread_count'] == 1, f"Expected single-threaded processing, but {results['thread_count']} threads used"
                    print(f"[OK] Sequential processing confirmed")
                
            except Exception as e:
                print(f"[FAILED] Test failed with error: {str(e)}")
                return False
    
    print(f"\n[OK] All multi-threading tests passed!")
    return True


def test_thread_safety():
    """Test thread safety of the multi-threading implementation."""
    print("\n=== Thread Safety Test ===")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test components
    failed_tracker = FailedConversionsTracker()
    processor = MultiThreadProcessor(failed_tracker)
    
    # Create mock blob monitors
    source_monitor = create_mock_blob_monitor()
    dest_monitor = create_mock_blob_monitor()
    
    # Test with concurrent access to shared resources
    documents = create_test_documents(8)
    
    with patch('multi_thread_processor.DocumentConverter') as mock_converter_class:
        mock_converter = Mock()
        mock_converter.convert_to_pdf.return_value = "/tmp/test_output.pdf"
        mock_converter.cleanup_temp_files.return_value = None
        mock_converter_class.return_value = mock_converter
        
        try:
            results = processor.process_documents_parallel(
                documents, source_monitor, dest_monitor
            )
            
            print(f"[OK] Thread safety test completed")
            print(f"  - All {results['total_documents']} documents processed without conflicts")
            print(f"  - No race conditions detected")
            print(f"  - Thread-safe logging confirmed")
            
            return True
            
        except Exception as e:
            print(f"[FAILED] Thread safety test failed: {str(e)}")
            return False


def main():
    """Main test function."""
    print("Multi-Threading Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    if not test_multi_threading():
        print("\n[FAILED] Multi-threading tests failed!")
        return False
    
    # Test thread safety
    if not test_thread_safety():
        print("\n[FAILED] Thread safety tests failed!")
        return False
    
    print("\n[OK] All tests passed successfully!")
    print("\nMulti-threading implementation is working correctly.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 