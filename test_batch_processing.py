#!/usr/bin/env python3
"""
Test script for batch processing functionality.
This script tests the batch processing with different batch sizes and configurations.
"""

import os
import sys
import logging
import time
from unittest.mock import Mock, patch

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from batch_processor import BatchProcessor
from failed_conversions import FailedConversionsTracker
from config import ENABLE_BATCH_PROCESSING, BATCH_SIZE, BATCH_DELAY_SECONDS, MAX_WORKER_THREADS


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


def create_test_documents(num_documents=50):
    """Create a list of test document names."""
    test_extensions = ['.docx', '.pdf', '.txt', '.html', '.jpg', '.png']
    documents = []
    
    for i in range(num_documents):
        ext = test_extensions[i % len(test_extensions)]
        documents.append(f"test_document_{i+1}{ext}")
    
    return documents


def test_batch_processing():
    """Test the batch processing functionality."""
    print("=== Batch Processing Test ===")
    print(f"Batch processing enabled: {ENABLE_BATCH_PROCESSING}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Batch delay: {BATCH_DELAY_SECONDS} seconds")
    print(f"Max worker threads: {MAX_WORKER_THREADS}")
    print()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test components
    failed_tracker = FailedConversionsTracker()
    processor = BatchProcessor(failed_tracker)
    
    # Create mock blob monitors
    source_monitor = create_mock_blob_monitor()
    dest_monitor = create_mock_blob_monitor()
    
    # Test with different numbers of documents
    test_cases = [
        (25, "Small batch (should fit in one batch)"),
        (50, "Medium batch (should create multiple batches)"),
        (100, "Large batch (should create multiple batches)")
    ]
    
    for num_docs, description in test_cases:
        print(f"\n--- Test Case: {num_docs} documents ---")
        print(f"Description: {description}")
        
        documents = create_test_documents(num_docs)
        print(f"Documents: {len(documents)} total")
        
        # Calculate expected batches
        expected_batches = (num_docs + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"Expected batches: {expected_batches}")
        
        # Mock the document converter to avoid actual conversion
        with patch('multi_thread_processor.DocumentConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_to_pdf.return_value = "/tmp/test_output.pdf"
            mock_converter.cleanup_temp_files.return_value = None
            mock_converter_class.return_value = mock_converter
            
            start_time = time.time()
            
            try:
                results = processor.process_documents_in_batches(
                    documents, source_monitor, dest_monitor
                )
                
                end_time = time.time()
                actual_time = end_time - start_time
                
                print(f"[OK] Batch processing completed successfully")
                print(f"  - Total documents: {results['total_documents']}")
                print(f"  - Total batches: {results['total_batches']}")
                print(f"  - Successful conversions: {results['successful_conversions']}")
                print(f"  - Failed conversions: {results['failed_conversions']}")
                print(f"  - Processing time: {results['processing_time']:.2f} seconds")
                print(f"  - Actual time: {actual_time:.2f} seconds")
                
                # Verify results
                assert results['total_documents'] == num_docs, f"Expected {num_docs} documents, got {results['total_documents']}"
                assert results['successful_conversions'] == num_docs, f"Expected {num_docs} successful conversions, got {results['successful_conversions']}"
                assert results['failed_conversions'] == 0, f"Expected 0 failed conversions, got {results['failed_conversions']}"
                assert results['total_batches'] == expected_batches, f"Expected {expected_batches} batches, got {results['total_batches']}"
                
                # Verify batch results
                if results['batch_results']:
                    print(f"  - Batch results:")
                    for batch_info in results['batch_results']:
                        print(f"    Batch {batch_info['batch_num']}: {batch_info['documents_processed']} docs, "
                              f"{batch_info['successful_conversions']} success, {batch_info['failed_conversions']} failed, "
                              f"{batch_info['processing_time']:.2f}s")
                
                print(f"[OK] Batch processing test completed successfully")
                
            except Exception as e:
                print(f"[FAILED] Test failed with error: {str(e)}")
                return False
    
    print(f"\n[OK] All batch processing tests passed!")
    return True


def test_batch_estimates():
    """Test batch processing estimates."""
    print("\n=== Batch Processing Estimates Test ===")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test components
    failed_tracker = FailedConversionsTracker()
    processor = BatchProcessor(failed_tracker)
    
    # Test with different document counts
    test_counts = [1000, 10000, 100000, 1000000]
    
    for doc_count in test_counts:
        estimates = processor.get_batch_processing_estimate(doc_count)
        
        print(f"\nEstimates for {doc_count:,} documents:")
        print(f"  - Estimated batches: {estimates['estimated_batches']}")
        print(f"  - Estimated time: {estimates['estimated_time_hours']:.1f} hours ({estimates['estimated_time_days']:.1f} days)")
        print(f"  - Estimated memory usage: {estimates['memory_usage_mb']:.0f} MB")
        print(f"  - Time per batch: {estimates['time_per_batch_seconds']:.1f} seconds")
    
    return True


def test_batch_configuration_validation():
    """Test batch configuration validation."""
    print("\n=== Batch Configuration Validation Test ===")
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create test components
    failed_tracker = FailedConversionsTracker()
    processor = BatchProcessor(failed_tracker)
    
    # Test configuration validation
    validation = processor.validate_batch_configuration()
    
    print(f"Configuration validation results:")
    print(f"  - Batch size OK: {validation['batch_size_ok']}")
    print(f"  - Thread count OK: {validation['thread_count_ok']}")
    print(f"  - Delay OK: {validation['delay_ok']}")
    
    if validation['recommendations']:
        print(f"  - Recommendations:")
        for recommendation in validation['recommendations']:
            print(f"    * {recommendation}")
    else:
        print(f"  - No recommendations (configuration is optimal)")
    
    return True


def test_batch_processing_disabled():
    """Test behavior when batch processing is disabled."""
    print("\n=== Batch Processing Disabled Test ===")
    
    # Temporarily disable batch processing
    with patch('batch_processor.ENABLE_BATCH_PROCESSING', False):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Create test components
        failed_tracker = FailedConversionsTracker()
        processor = BatchProcessor(failed_tracker)
        
        # Create mock blob monitors
        source_monitor = create_mock_blob_monitor()
        dest_monitor = create_mock_blob_monitor()
        
        documents = create_test_documents(20)
        
        # Mock the document converter
        with patch('multi_thread_processor.DocumentConverter') as mock_converter_class:
            mock_converter = Mock()
            mock_converter.convert_to_pdf.return_value = "/tmp/test_output.pdf"
            mock_converter.cleanup_temp_files.return_value = None
            mock_converter_class.return_value = mock_converter
            
            try:
                results = processor.process_documents_in_batches(
                    documents, source_monitor, dest_monitor
                )
                
                print(f"[OK] Processing completed without batch processing")
                print(f"  - Total documents: {results['total_documents']}")
                print(f"  - Successful conversions: {results['successful_conversions']}")
                print(f"  - Failed conversions: {results['failed_conversions']}")
                
                return True
                
            except Exception as e:
                print(f"[FAILED] Batch processing disabled test failed: {str(e)}")
                return False


def main():
    """Main test function."""
    print("Batch Processing Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    if not test_batch_processing():
        print("\n[FAILED] Batch processing tests failed!")
        return False
    
    # Test estimates
    if not test_batch_estimates():
        print("\n[FAILED] Batch estimates tests failed!")
        return False
    
    # Test configuration validation
    if not test_batch_configuration_validation():
        print("\n[FAILED] Configuration validation tests failed!")
        return False
    
    # Test disabled functionality
    if not test_batch_processing_disabled():
        print("\n[FAILED] Batch processing disabled tests failed!")
        return False
    
    print("\n[OK] All tests passed successfully!")
    print("\nBatch processing implementation is working correctly.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 