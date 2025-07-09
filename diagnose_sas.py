#!/usr/bin/env python3
"""
Diagnostic script to analyze SAS URL and test different authentication methods.
"""

import urllib.parse
from urllib.parse import urlparse, parse_qs
from azure.storage.blob import BlobServiceClient
from azure.core.pipeline.transport import RequestsTransport
from config import SAS_URL, CONNECTION_POOL_SIZE, CONNECTION_POOL_MAX_RETRIES, CONNECTION_POOL_TIMEOUT

def analyze_sas_url():
    """Analyze the SAS URL structure and parameters."""
    print("=== SAS URL Analysis ===")
    print(f"Original URL: {SAS_URL}")
    
    parsed = urlparse(SAS_URL)
    print(f"Scheme: {parsed.scheme}")
    print(f"Netloc: {parsed.netloc}")
    print(f"Path: {parsed.path}")
    print(f"Query: {parsed.query}")
    
    # Parse query parameters
    params = parse_qs(parsed.query)
    print("\nQuery Parameters:")
    for key, values in params.items():
        print(f"  {key}: {values[0]}")
    
    # Check required parameters
    required = ['sv', 'sig']
    missing = [param for param in required if param not in params]
    if missing:
        print(f"\n[FAILED] Missing required parameters: {missing}")
    else:
        print(f"\n[OK] All required parameters present")
    
    return parsed, params

def test_authentication_methods(parsed_url, params):
    """Test different authentication methods with connection pool configuration."""
    print("\n=== Testing Authentication Methods ===")
    
    account_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    container_name = parsed_url.path.strip('/')
    
    # Configure connection pool settings
    transport = RequestsTransport(
        connection_pool_size=CONNECTION_POOL_SIZE,
        max_retries=CONNECTION_POOL_MAX_RETRIES,
        timeout=CONNECTION_POOL_TIMEOUT
    )
    
    methods = [
        ("Method 1: Direct SAS URL", lambda: BlobServiceClient(
            account_url=account_url,
            credential=SAS_URL,
            transport=transport
        )),
        
        ("Method 2: SAS URL as credential", lambda: BlobServiceClient(
            account_url=account_url,
            credential=SAS_URL,
            transport=transport
        )),
        
        ("Method 3: Connection string", lambda: BlobServiceClient.from_connection_string(
            f"BlobEndpoint={account_url};SharedAccessSignature={parsed_url.query}",
            transport=transport
        )),
        
        ("Method 4: Reconstructed URL", lambda: BlobServiceClient(
            account_url=account_url,
            credential=f"{account_url}/{container_name}?{parsed_url.query}",
            transport=transport
        ))
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"\nTesting {method_name}...")
            client = method_func()
            
            # Test the connection
            container_client = client.get_container_client(container_name)
            blobs = list(container_client.list_blobs())
            print(f"[OK] {method_name} - SUCCESS! Found {len(blobs)} blobs")
            return client
            
        except Exception as e:
            print(f"[FAILED] {method_name} - FAILED: {str(e)}")
    
    return None

def test_url_encoding():
    """Test URL encoding issues."""
    print("\n=== URL Encoding Test ===")
    
    # Test if the signature needs different encoding
    parsed = urlparse(SAS_URL)
    original_sig = parse_qs(parsed.query).get('sig', [''])[0]
    
    print(f"Original signature: {original_sig}")
    print(f"URL decoded: {urllib.parse.unquote(original_sig)}")
    print(f"Double URL decoded: {urllib.parse.unquote(urllib.parse.unquote(original_sig))}")
    
    # Test different encoding methods
    test_signatures = [
        original_sig,
        urllib.parse.unquote(original_sig),
        urllib.parse.quote(original_sig),
        urllib.parse.quote(urllib.parse.unquote(original_sig))
    ]
    
    for i, sig in enumerate(test_signatures, 1):
        print(f"Test signature {i}: {sig}")

if __name__ == "__main__":
    print("SAS URL Diagnostic Tool")
    print("=" * 50)
    
    # Analyze the SAS URL
    parsed_url, params = analyze_sas_url()
    
    # Test URL encoding
    test_url_encoding()
    
    # Test authentication methods
    client = test_authentication_methods(parsed_url, params)
    
    if client:
        print("\n[OK] Authentication successful!")
    else:
        print("\n[FAILED] All authentication methods failed")
        print("\nPossible solutions:")
        print("1. Check if the SAS URL has expired")
        print("2. Verify the SAS URL has the correct permissions (read, write, list)")
        print("3. Ensure the SAS URL was generated for the correct container")
        print("4. Try generating a new SAS URL with fresh permissions") 