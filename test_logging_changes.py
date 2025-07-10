#!/usr/bin/env python3
"""
Test script to demonstrate the logging changes.
This script shows the difference between INFO and DEBUG level logging.
"""

import logging
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LOG_LEVEL

def test_logging_levels():
    """Test the different logging levels."""
    print("=== Logging Level Test ===")
    print(f"Current LOG_LEVEL from config: {LOG_LEVEL}")
    print()
    
    # Setup logging with the configured level
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('test')
    
    print("Testing different log levels:")
    print("-" * 50)
    
    # Test INFO level messages (should be visible)
    logger.info("This is an INFO message - should be visible")
    logger.info("[OK] Document processing started")
    logger.info("[OK] Multi-threading enabled with 16 max threads")
    
    # Test DEBUG level messages (should be visible with DEBUG level)
    logger.debug("This is a DEBUG message - should be visible with DEBUG level")
    logger.debug("Downloaded document.docx to temp/document.docx")
    logger.debug("Uploaded temp/document.pdf as converted/document.pdf")
    logger.debug("Deleted downloaded file to conserve space: document.docx")
    logger.debug("Cleaned up temporary file: temp/document.docx")
    
    # Test ERROR level messages (should always be visible)
    logger.error("This is an ERROR message - should always be visible")
    logger.error("[FAILED] Failed to download document.docx from source")
    
    print("-" * 50)
    print("Note: With LOG_LEVEL=DEBUG, all messages (INFO, DEBUG, ERROR) are visible.")
    print("With LOG_LEVEL=INFO, only INFO and ERROR messages would be visible.")
    print("With LOG_LEVEL=WARNING, only WARNING and ERROR messages would be visible.")

def test_progress_bar_only():
    """Test that progress bars work without verbose logging."""
    print("\n=== Progress Bar Test ===")
    print("Progress bars should work independently of logging level.")
    print("Only progress bars will be shown, not individual file operations.")
    
    try:
        from tqdm import tqdm
        print("tqdm available - progress bars will work")
        
        # Simulate a progress bar
        with tqdm(total=5, desc="Converting documents", unit="doc") as pbar:
            for i in range(5):
                # Simulate processing
                import time
                time.sleep(0.1)
                pbar.update(1)
                pbar.set_description(f"Converting document_{i+1}.docx")
        
        print("Progress bar test completed successfully")
        
    except ImportError:
        print("tqdm not available - progress bars will not work")
        print("Install with: pip install tqdm")

if __name__ == "__main__":
    test_logging_levels()
    test_progress_bar_only()
    
    print("\n=== Summary ===")
    print("Changes made:")
    print("1. LOG_LEVEL changed from 'INFO' to 'DEBUG' in config.py")
    print("2. Verbose operations (download, upload, delete) moved to DEBUG level")
    print("3. Progress bars remain independent of logging level")
    print("4. Important status messages remain at INFO level")
    print("5. Error messages remain at ERROR level")
    print("\nTo see only progress bars without debug messages:")
    print("Change LOG_LEVEL back to 'INFO' in config.py") 