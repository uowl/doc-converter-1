#!/usr/bin/env python3
"""
Test script to verify SAS URL path parsing for different URL formats.
"""

from sas_url_handler import SASUrlHandler

def test_sas_url_parsing():
    """Test SAS URL parsing with different path formats."""
    
    # Test cases
    test_cases = [
        {
            "name": "Simple container URL",
            "url": "https://account.blob.core.windows.net/container?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123",
            "expected_container": "container",
            "expected_path": ""
        },
        {
            "name": "URL pointing to specific folder",
            "url": "https://account.blob.core.windows.net/container/root/folder1?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123",
            "expected_container": "container",
            "expected_path": "root/folder1"
        },
        {
            "name": "URL pointing to single folder",
            "url": "https://account.blob.core.windows.net/container/project1?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123",
            "expected_container": "container",
            "expected_path": "project1"
        },
        {
            "name": "URL pointing to nested folder",
            "url": "https://account.blob.core.windows.net/container/org/department/team/project?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123",
            "expected_container": "container",
            "expected_path": "org/department/team/project"
        },
        {
            "name": "URL pointing to folder named 'config'",
            "url": "https://account.blob.core.windows.net/container/root/folder1/config?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=test123",
            "expected_container": "container",
            "expected_path": "root/folder1/config"
        }
    ]
    
    print("=== Testing SAS URL Path Parsing ===")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"URL: {test_case['url']}")
        
        try:
            handler = SASUrlHandler(test_case['url'])
            account_info = handler.get_account_info()
            
            print(f"Parsed container: {account_info['container_name']}")
            print(f"Parsed additional path: {account_info['additional_path']}")
            print(f"Full path prefix: {handler.get_full_path_prefix()}")
            
            # Verify results
            if account_info['container_name'] == test_case['expected_container']:
                print("✅ Container name matches expected")
            else:
                print(f"❌ Container name mismatch. Expected: {test_case['expected_container']}, Got: {account_info['container_name']}")
            
            if account_info['additional_path'] == test_case['expected_path']:
                print("✅ Additional path matches expected")
            else:
                print(f"❌ Additional path mismatch. Expected: {test_case['expected_path']}, Got: {account_info['additional_path']}")
            
            # Test path construction
            test_folder = "config"
            full_path = handler.get_full_path_prefix()
            if full_path:
                expected_full_path = f"{full_path}/{test_folder}"
            else:
                expected_full_path = test_folder
            
            print(f"Example path construction: {test_folder} -> {expected_full_path}")
            
        except Exception as e:
            print(f"❌ Error parsing URL: {str(e)}")
        
        print("-" * 80)
        print()

def test_path_construction():
    """Test path construction for different scenarios."""
    
    print("=== Testing Path Construction ===")
    print()
    
    # Test different URL formats
    test_urls = [
        "https://account.blob.core.windows.net/container?sp=racwdl&sig=test123",
        "https://account.blob.core.windows.net/container/project1?sp=racwdl&sig=test123",
        "https://account.blob.core.windows.net/container/org/dept/team?sp=racwdl&sig=test123"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"Test URL {i}: {url}")
        
        try:
            handler = SASUrlHandler(url)
            account_info = handler.get_account_info()
            
            print(f"Container: {account_info['container_name']}")
            print(f"Additional path: {account_info['additional_path']}")
            
            # Test folder path construction
            folders = ["config", "files", "converted"]
            for folder in folders:
                if account_info['additional_path']:
                    full_path = f"{account_info['additional_path']}/{folder}"
                else:
                    full_path = folder
                print(f"  {folder} -> {full_path}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

if __name__ == "__main__":
    test_sas_url_parsing()
    test_path_construction()
    
    print("=== Summary ===")
    print("The SAS URL handler now supports:")
    print("1. Simple container URLs (existing functionality)")
    print("2. URLs with additional path components after the container name")
    print("3. Automatic path construction for config, files, and converted folders")
    print("4. Proper handling of nested folder structures") 