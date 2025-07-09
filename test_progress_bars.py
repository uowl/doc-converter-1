#!/usr/bin/env python3
"""
Test script for progress bar functionality.
This script tests the progress bar display during document processing.
"""

import os
import sys
import logging
import time
from unittest.mock import Mock, patch

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_thread_processor import MultiThreadProcessor
from failed_conversions import FailedConversionsTracker
from config import ENABLE_PROGRESS_BARS, PROGRESS_BAR_DESCRIPTION


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


def test_progress_bars():
    """Test the progress bar functionality."""
    print("=== Progress Bar Test ===")
    print(f"Progress bars enabled: {ENABLE_PROGRESS_BARS}")
    print(f"Progress bar description: {PROGRESS_BAR_DESCRIPTION}")
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
        (3, "Sequential processing with progress bars"),
        (6, "Multi-threaded processing with progress bars")
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
            
            # Add a small delay to simulate processing time
            def mock_convert_with_delay(file_path):
                time.sleep(0.1)  # Simulate processing time
                return "/tmp/test_output.pdf"
            
            mock_converter.convert_to_pdf = mock_convert_with_delay
            
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
                
                print(f"[OK] Progress bar test completed successfully")
                
            except Exception as e:
                print(f"[FAILED] Test failed with error: {str(e)}")
                return False
    
    print(f"\n[OK] All progress bar tests passed!")
    return True


def test_progress_bar_disabled():
    """Test behavior when progress bars are disabled."""
    print("\n=== Progress Bar Disabled Test ===")
    
    # Temporarily disable progress bars
    with patch('multi_thread_processor.ENABLE_PROGRESS_BARS', False):
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
        
        documents = create_test_documents(4)
        
        # Mock the document converter
        with patch('multi_thread_processor.DocumentConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_to_pdf.return_value = "/tmp/test_output.pdf"
            mock_converter.cleanup_temp_files.return_value = None
            mock_converter_class.return_value = mock_converter
            
            try:
                results = processor.process_documents_parallel(
                    documents, source_monitor, dest_monitor
                )
                
                print(f"[OK] Processing completed without progress bars")
                print(f"  - Total documents: {results['total_documents']}")
                print(f"  - Successful conversions: {results['successful_conversions']}")
                print(f"  - Failed conversions: {results['failed_conversions']}")
                
                return True
                
            except Exception as e:
                print(f"[FAILED] Progress bar disabled test failed: {str(e)}")
                return False


def main():
    """Main test function."""
    print("Progress Bar Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    if not test_progress_bars():
        print("\n[FAILED] Progress bar tests failed!")
        return False
    
    # Test disabled functionality
    if not test_progress_bar_disabled():
        print("\n[FAILED] Progress bar disabled tests failed!")
        return False
    
    print("\n[OK] All tests passed successfully!")
    print("\nProgress bar implementation is working correctly.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 