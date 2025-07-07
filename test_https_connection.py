#!/usr/bin/env python3
"""
Test HTTPS connection to Azure Blob Storage.
"""

import requests
from urllib.parse import urlparse
from config import SAS_URL

def test_https_connection():
    """Test HTTPS connection to the blob storage."""
    print("Testing HTTPS connection to Azure Blob Storage...")
    
    # Parse the SAS URL
    parsed_url = urlparse(SAS_URL)
    account_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    print(f"Account URL: {account_url}")
    print(f"Protocol: {parsed_url.scheme}")
    print(f"Host: {parsed_url.netloc}")
    print(f"Container: {parsed_url.path.strip('/')}")
    
    # Test basic HTTPS connection
    try:
        response = requests.get(account_url, timeout=10)
        print(f"✓ HTTPS connection successful (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"✗ HTTPS connection failed: {str(e)}")
        return False
    
    # Test with SAS URL
    try:
        response = requests.get(SAS_URL, timeout=10)
        print(f"✓ SAS URL connection successful (Status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ SAS URL connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_https_connection() 