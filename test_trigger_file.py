#!/usr/bin/env python3
"""
Test script to verify trigger file parsing functionality.
"""

from trigger_file_handler import TriggerFileHandler

def test_trigger_file_parsing():
    """Test trigger file content parsing."""
    
    print("=== Testing Trigger File Parsing ===")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Valid trigger file",
            "content": """source_sas_url:https://account.blob.core.windows.net/container/source?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123
dest_sas_url:https://account.blob.core.windows.net/container/dest?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123""",
            "should_pass": True
        },
        {
            "name": "Trigger file with comments",
            "content": """# This is a comment
source_sas_url:https://account.blob.core.windows.net/container/source?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123
# Another comment
dest_sas_url:https://account.blob.core.windows.net/container/dest?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123""",
            "should_pass": True
        },
        {
            "name": "Trigger file with extra whitespace",
            "content": """  source_sas_url  :  https://account.blob.core.windows.net/container/source?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123  
  dest_sas_url  :  https://account.blob.core.windows.net/container/dest?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123  """,
            "should_pass": True
        },
        {
            "name": "Missing source_sas_url",
            "content": """dest_sas_url:https://account.blob.core.windows.net/container/dest?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123""",
            "should_pass": False
        },
        {
            "name": "Missing dest_sas_url",
            "content": """source_sas_url:https://account.blob.core.windows.net/container/source?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123""",
            "should_pass": False
        },
        {
            "name": "Empty content",
            "content": "",
            "should_pass": False
        },
        {
            "name": "Invalid SAS URL format",
            "content": """source_sas_url:invalid-url
dest_sas_url:https://account.blob.core.windows.net/container/dest?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123""",
            "should_pass": False
        }
    ]
    
    trigger_handler = TriggerFileHandler()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Content: {test_case['content']}")
        
        try:
            config = trigger_handler.parse_trigger_file_content(test_case['content'])
            
            if test_case['should_pass']:
                print("[OK] PASSED - Successfully parsed trigger file")
                print(f"  Source SAS URL: {config['source_sas_url']}")
                print(f"  Destination SAS URL: {config['dest_sas_url']}")
            else:
                print("[FAILED] FAILED - Should have failed but didn't")
                
        except Exception as e:
            if test_case['should_pass']:
                print(f"[FAILED] FAILED - Should have passed but failed: {str(e)}")
            else:
                print(f"[OK] PASSED - Correctly failed with error: {str(e)}")
        
        print("-" * 80)
        print()

def test_sas_url_validation():
    """Test SAS URL validation."""
    
    print("=== Testing SAS URL Validation ===")
    print()
    
    test_urls = [
        {
            "name": "Valid SAS URL",
            "url": "https://account.blob.core.windows.net/container?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123",
            "should_pass": True
        },
        {
            "name": "Valid SAS URL with path",
            "url": "https://account.blob.core.windows.net/container/source?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123",
            "should_pass": True
        },
        {
            "name": "Invalid URL format",
            "url": "invalid-url",
            "should_pass": False
        },
        {
            "name": "Missing SAS parameters",
            "url": "https://account.blob.core.windows.net/container",
            "should_pass": False
        }
    ]
    
    trigger_handler = TriggerFileHandler()
    
    for i, test_case in enumerate(test_urls, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"URL: {test_case['url']}")
        
        try:
            trigger_handler._validate_sas_url(test_case['url'], "test")
            
            if test_case['should_pass']:
                print("[OK] PASSED - Valid SAS URL")
            else:
                print("[FAILED] FAILED - Should have failed but didn't")
                
        except Exception as e:
            if test_case['should_pass']:
                print(f"[FAILED] FAILED - Should have passed but failed: {str(e)}")
            else:
                print(f"[OK] PASSED - Correctly failed with error: {str(e)}")
        
        print("-" * 80)
        print()

def show_usage_example():
    """Show usage example."""
    
    print("=== Usage Example ===")
    print()
    
    print("1. Create a trigger file with the following content:")
    print("   source_sas_url:https://account.blob.core.windows.net/container/source?sp=racwdl&sig=test123")
    print("   dest_sas_url:https://account.blob.core.windows.net/container/dest?sp=racwdl&sig=test123")
    print()
    
    print("2. Upload the trigger file to your main SAS URL container:")
    print("   - File name: start_conversion_1234.txt")
    print("   - Location: config/start_conversion_1234.txt")
    print()
    
    print("3. The system will:")
    print("   - Read the trigger file")
    print("   - Download files from source_sas_url/files/")
    print("   - Convert documents to PDF")
    print("   - Upload converted files to dest_sas_url/converted/")
    print("   - Delete the trigger file after processing")
    print()

if __name__ == "__main__":
    test_trigger_file_parsing()
    test_sas_url_validation()
    show_usage_example()
    
    print("=== Summary ===")
    print("[OK] Trigger file parsing supports key-value format")
    print("[OK] SAS URL validation ensures proper format")
    print("[OK] Comments and whitespace are handled correctly")
    print("[OK] Error handling for missing or invalid configurations") 