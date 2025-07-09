#!/usr/bin/env python3
"""
Example script demonstrating different SAS URL formats and their folder structures.
"""

from sas_url_handler import SASUrlHandler

def demonstrate_sas_url_formats():
    """Demonstrate different SAS URL formats and their folder structures."""
    
    print("=== SAS URL Format Examples ===")
    print()
    
    # Example 1: Simple container URL
    print("1. Simple Container URL")
    print("URL: https://account.blob.core.windows.net/container?sp=racwdl&sig=test123")
    print()
    print("Expected folder structure:")
    print("container/")
    print("├── config/")
    print("│   └── start_converson_1234.txt")
    print("├── files/")
    print("│   ├── document1.docx")
    print("│   └── document2.pdf")
    print("└── converted/")
    print("    ├── document1.pdf")
    print("    └── document2.pdf")
    print()
    
    # Example 2: URL pointing to a specific folder
    print("2. URL Pointing to Specific Folder")
    print("URL: https://account.blob.core.windows.net/container/root/folder1?sp=racwdl&sig=test123")
    print()
    print("Expected folder structure:")
    print("container/")
    print("└── root/")
    print("    └── folder1/")
    print("        ├── config/")
    print("        │   └── start_converson_1234.txt")
    print("        ├── files/")
    print("        │   ├── document1.docx")
    print("        │   └── document2.pdf")
    print("        └── converted/")
    print("            ├── document1.pdf")
    print("            └── document2.pdf")
    print()
    
    # Example 3: URL pointing to a nested folder
    print("3. URL Pointing to Nested Folder")
    print("URL: https://account.blob.core.windows.net/container/org/department/team/project?sp=racwdl&sig=test123")
    print()
    print("Expected folder structure:")
    print("container/")
    print("└── org/")
    print("    └── department/")
    print("        └── team/")
    print("            └── project/")
    print("                ├── config/")
    print("                │   └── start_converson_1234.txt")
    print("                ├── files/")
    print("                │   ├── document1.docx")
    print("                │   └── document2.pdf")
    print("                └── converted/")
    print("                    ├── document1.pdf")
    print("                    └── document2.pdf")
    print()
    
    # Example 4: URL pointing to a folder named 'config'
    print("4. URL Pointing to Folder Named 'config'")
    print("URL: https://account.blob.core.windows.net/container/root/folder1/config?sp=racwdl&sig=test123")
    print()
    print("Expected folder structure:")
    print("container/")
    print("└── root/")
    print("    └── folder1/")
    print("        └── config/")
    print("            ├── config/")
    print("            │   └── start_converson_1234.txt")
    print("            ├── files/")
    print("            │   ├── document1.docx")
    print("            │   └── document2.pdf")
    print("            └── converted/")
    print("                ├── document1.pdf")
    print("                └── document2.pdf")
    print()

def test_url_parsing():
    """Test URL parsing with example URLs."""
    
    print("=== URL Parsing Test ===")
    print()
    
    test_urls = [
        {
            "name": "Simple Container",
            "url": "https://account.blob.core.windows.net/container?sp=racwdl&sig=test123",
            "description": "Direct container access"
        },
        {
            "name": "Specific Folder",
            "url": "https://account.blob.core.windows.net/container/project1?sp=racwdl&sig=test123",
            "description": "URL pointing to specific folder that contains config/files/converted"
        },
        {
            "name": "Nested Folder",
            "url": "https://account.blob.core.windows.net/container/org/dept/team?sp=racwdl&sig=test123",
            "description": "URL pointing to nested folder structure"
        },
        {
            "name": "Folder Named Config",
            "url": "https://account.blob.core.windows.net/container/root/folder1/config?sp=racwdl&sig=test123",
            "description": "URL pointing to folder named 'config' that contains config/files/converted"
        }
    ]
    
    for test_case in test_urls:
        print(f"Test: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"URL: {test_case['url']}")
        
        try:
            handler = SASUrlHandler(test_case['url'])
            account_info = handler.get_account_info()
            
            print(f"Parsed container: {account_info['container_name']}")
            print(f"Additional path: {account_info['additional_path']}")
            
            # Show folder paths
            if account_info['additional_path']:
                config_path = f"{account_info['additional_path']}/config"
                files_path = f"{account_info['additional_path']}/files"
                converted_path = f"{account_info['additional_path']}/converted"
            else:
                config_path = "config"
                files_path = "files"
                converted_path = "converted"
            
            print(f"Config folder: {config_path}")
            print(f"Files folder: {files_path}")
            print(f"Converted folder: {converted_path}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 60)
        print()

def show_usage_instructions():
    """Show usage instructions for different URL formats."""
    
    print("=== Usage Instructions ===")
    print()
    
    print("1. For simple container URLs:")
    print("   - Upload trigger file to: container/config/start_converson_1234.txt")
    print("   - Upload documents to: container/files/")
    print("   - Converted files will be in: container/converted/")
    print()
    
    print("2. For URLs with additional paths:")
    print("   - Upload trigger file to: container/additional/path/config/start_converson_1234.txt")
    print("   - Upload documents to: container/additional/path/files/")
    print("   - Converted files will be in: container/additional/path/converted/")
    print()
    
    print("3. Configuration:")
    print("   - Update SAS_URL in config.py with your URL")
    print("   - The system automatically detects the URL format")
    print("   - No changes needed to AZURE_CONFIG_FOLDER or AZURE_FILES_FOLDER settings")
    print()

if __name__ == "__main__":
    demonstrate_sas_url_formats()
    test_url_parsing()
    show_usage_instructions()
    
    print("=== Summary ===")
    print("[OK] The application now supports SAS URLs with embedded folder paths")
    print("[OK] Automatic path detection and construction")
    print("[OK] Backward compatibility with simple container URLs")
    print("[OK] No configuration changes required for existing setups") 