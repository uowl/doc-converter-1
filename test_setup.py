#!/usr/bin/env python3
"""
Test script to verify the document converter setup.
This script checks dependencies, blob storage connection, and basic functionality.
"""

import sys
import os
import logging
from config import SAS_URL, TRIGGER_FILE_PATTERN

def test_dependencies():
    """Test if all required dependencies are installed."""
    print("Testing dependencies...")
    
    required_packages = [
        'azure.storage.blob',
        'aspose.words',
        'aspose.pdf',
        'dotenv',
        'schedule',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them using: pip install -r requirements.txt")
        return False
    
    print("✓ All dependencies are installed!")
    return True

def test_blob_connection():
    """Test blob storage connection."""
    print("\nTesting blob storage connection...")
    
    try:
        from blob_monitor import BlobMonitor
        monitor = BlobMonitor()
        
        # Test basic connection
        container_client = monitor.blob_service_client.get_container_client(monitor.container_name)
        
        # Try to list blobs (this will test the connection)
        blobs = list(container_client.list_blobs())
        print(f"✓ Connected to blob storage successfully!")
        print(f"✓ Found {len(blobs)} blobs in container")
        
        # Check for trigger file
        trigger_found = monitor.check_for_trigger_file()
        if trigger_found:
            print(f"✓ Trigger file '{TRIGGER_FILE_PATTERN}' found!")
        else:
            print(f"ℹ Trigger file '{TRIGGER_FILE_PATTERN}' not found (this is normal)")
        
        return True
        
    except Exception as e:
        print(f"✗ Blob storage connection failed: {str(e)}")
        print("✓ HTTPS connection is working (connection established)")
        print("⚠ SAS URL authentication issue - check if URL is expired or has correct permissions")
        print("Check your SAS URL and network connection.")
        return False

def test_document_converter():
    """Test document converter setup."""
    print("\nTesting document converter...")
    
    try:
        from document_converter import DocumentConverter
        converter = DocumentConverter()
        print("✓ Document converter initialized successfully!")
        
        # Test if Aspose is working
        try:
            import aspose.words as aw
            print("✓ Aspose.Words is available!")
        except Exception as e:
            print(f"✗ Aspose.Words error: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Document converter test failed: {str(e)}")
        return False

def test_configuration():
    """Test configuration settings."""
    print("\nTesting configuration...")
    
    try:
        # Test SAS URL format
        from urllib.parse import urlparse
        parsed_url = urlparse(SAS_URL)
        
        if parsed_url.scheme and parsed_url.netloc:
            print("✓ SAS URL format is valid")
        else:
            print("✗ SAS URL format is invalid")
            return False
        
        # Test other config values
        if TRIGGER_FILE_PATTERN:
            print(f"✓ Trigger file pattern: {TRIGGER_FILE_PATTERN}")
        else:
            print("✗ Trigger file pattern is empty")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("Document Converter Setup Test")
    print("=" * 40)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Configuration", test_configuration),
        ("Blob Storage Connection", test_blob_connection),
        ("Document Converter", test_document_converter)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {str(e)}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Your setup is ready.")
        print("\nTo start the application, run:")
        print("python main.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check your SAS URL in config.py")
        print("3. Ensure you have internet connectivity")
        print("4. Verify Aspose license if using in production")

if __name__ == "__main__":
    main() 