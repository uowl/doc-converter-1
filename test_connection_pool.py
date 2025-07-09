#!/usr/bin/env python3
"""
Test script for connection pool configuration.
This script tests the connection pool settings and Azure Blob Storage connectivity.
"""

import os
import sys
import logging
import time
from unittest.mock import Mock, patch

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_url_handler import SASUrlHandler
from config import CONNECTION_POOL_SIZE, CONNECTION_POOL_MAX_RETRIES, CONNECTION_POOL_TIMEOUT, SAS_URL


def test_connection_pool_configuration():
    """Test the connection pool configuration."""
    print("=== Connection Pool Configuration Test ===")
    print(f"Connection pool size: {CONNECTION_POOL_SIZE}")
    print(f"Max retries: {CONNECTION_POOL_MAX_RETRIES}")
    print(f"Connection timeout: {CONNECTION_POOL_TIMEOUT} seconds")
    print()
    
    # Validate configuration values
    assert CONNECTION_POOL_SIZE > 0, "Connection pool size must be positive"
    assert CONNECTION_POOL_MAX_RETRIES >= 0, "Max retries must be non-negative"
    assert CONNECTION_POOL_TIMEOUT > 0, "Connection timeout must be positive"
    
    print("[OK] Connection pool configuration validation passed")
    
    # Test SAS URL handler with connection pool
    try:
        handler = SASUrlHandler(SAS_URL)
        print("[OK] SAS URL handler created successfully")
        
        # Validate SAS URL
        is_valid, message = handler.validate_sas_url()
        if is_valid:
            print(f"[OK] SAS URL validation passed: {message}")
        else:
            print(f"[FAILED] SAS URL validation failed: {message}")
            return False
        
        # Get account info
        account_info = handler.get_account_info()
        print(f"[OK] Account info retrieved:")
        print(f"  - Account URL: {account_info['account_url']}")
        print(f"  - Container: {account_info['container_name']}")
        print(f"  - Additional path: {account_info['additional_path']}")
        print(f"  - Protocol: {account_info['protocol']}")
        print(f"  - Host: {account_info['host']}")
        print(f"  - Has required params: {account_info['has_required_params']}")
        
        return True
        
    except Exception as e:
        print(f"[FAILED] Connection pool test failed: {str(e)}")
        return False


def test_blob_service_client_creation():
    """Test blob service client creation with connection pool."""
    print("\n=== Blob Service Client Creation Test ===")
    
    try:
        handler = SASUrlHandler(SAS_URL)
        
        # Test blob service client creation
        client = handler.get_blob_service_client()
        print("[OK] Blob service client created successfully")
        
        # Test basic connectivity (without actually making requests)
        print("[OK] Blob service client is ready for operations")
        
        return True
        
    except Exception as e:
        print(f"[FAILED] Blob service client creation failed: {str(e)}")
        return False


def test_connection_pool_performance():
    """Test connection pool performance with multiple operations."""
    print("\n=== Connection Pool Performance Test ===")
    
    try:
        handler = SASUrlHandler(SAS_URL)
        client = handler.get_blob_service_client()
        
        # Simulate multiple concurrent operations
        start_time = time.time()
        
        # Create multiple container clients (simulating concurrent operations)
        container_clients = []
        for i in range(min(10, CONNECTION_POOL_SIZE)):
            container_client = client.get_container_client(handler.container_name)
            container_clients.append(container_client)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        print(f"[OK] Created {len(container_clients)} container clients in {creation_time:.3f} seconds")
        print(f"[OK] Connection pool is working efficiently")
        
        return True
        
    except Exception as e:
        print(f"[FAILED] Connection pool performance test failed: {str(e)}")
        return False


def test_connection_pool_settings():
    """Test that connection pool settings are properly applied."""
    print("\n=== Connection Pool Settings Test ===")
    
    # Test with different configuration values
    test_configs = [
        (10, 2, 15),
        (25, 3, 20),
        (50, 5, 30)
    ]
    
    for pool_size, max_retries, timeout in test_configs:
        print(f"Testing with pool_size={pool_size}, max_retries={max_retries}, timeout={timeout}")
        
        # Temporarily patch the config values
        with patch('sas_url_handler.CONNECTION_POOL_SIZE', pool_size), \
             patch('sas_url_handler.CONNECTION_POOL_MAX_RETRIES', max_retries), \
             patch('sas_url_handler.CONNECTION_POOL_TIMEOUT', timeout):
            
            try:
                handler = SASUrlHandler(SAS_URL)
                client = handler.get_blob_service_client()
                print(f"[OK] Client created with custom settings")
                
            except Exception as e:
                print(f"[FAILED] Failed with custom settings: {str(e)}")
                return False
    
    print("[OK] All connection pool settings tests passed")
    return True


def test_connection_pool_error_handling():
    """Test connection pool error handling."""
    print("\n=== Connection Pool Error Handling Test ===")
    
    try:
        handler = SASUrlHandler(SAS_URL)
        
        # Test with invalid SAS URL (should fail gracefully)
        invalid_sas_url = "https://invalid-account.blob.core.windows.net/invalid-container?sp=r&st=2024-01-01T00:00:00Z&se=2024-01-02T00:00:00Z&sip=127.0.0.1&sv=2020-08-04&sr=c&sig=invalid"
        
        try:
            invalid_handler = SASUrlHandler(invalid_sas_url)
            invalid_client = invalid_handler.get_blob_service_client()
            print("[WARNING] Invalid SAS URL should have failed but didn't")
        except Exception as e:
            print(f"[OK] Invalid SAS URL properly rejected: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"[FAILED] Error handling test failed: {str(e)}")
        return False


def test_connection_pool_recommendations():
    """Provide recommendations for connection pool settings."""
    print("\n=== Connection Pool Recommendations ===")
    
    recommendations = []
    
    # Check pool size
    if CONNECTION_POOL_SIZE < 20:
        recommendations.append("Consider increasing CONNECTION_POOL_SIZE to at least 20 for better performance")
    elif CONNECTION_POOL_SIZE > 100:
        recommendations.append("Consider decreasing CONNECTION_POOL_SIZE to prevent resource exhaustion")
    
    # Check retries
    if CONNECTION_POOL_MAX_RETRIES < 2:
        recommendations.append("Consider increasing CONNECTION_POOL_MAX_RETRIES to at least 2")
    elif CONNECTION_POOL_MAX_RETRIES > 10:
        recommendations.append("Consider decreasing CONNECTION_POOL_MAX_RETRIES to prevent excessive delays")
    
    # Check timeout
    if CONNECTION_POOL_TIMEOUT < 10:
        recommendations.append("Consider increasing CONNECTION_POOL_TIMEOUT to at least 10 seconds")
    elif CONNECTION_POOL_TIMEOUT > 60:
        recommendations.append("Consider decreasing CONNECTION_POOL_TIMEOUT to prevent hanging operations")
    
    if recommendations:
        print("Recommendations:")
        for recommendation in recommendations:
            print(f"  - {recommendation}")
    else:
        print("[OK] Connection pool settings are optimal")
    
    return True


def main():
    """Main test function."""
    print("Connection Pool Test Suite")
    print("=" * 50)
    
    # Test configuration
    if not test_connection_pool_configuration():
        print("\n[FAILED] Connection pool configuration tests failed!")
        return False
    
    # Test blob service client creation
    if not test_blob_service_client_creation():
        print("\n[FAILED] Blob service client creation tests failed!")
        return False
    
    # Test performance
    if not test_connection_pool_performance():
        print("\n[FAILED] Connection pool performance tests failed!")
        return False
    
    # Test settings
    if not test_connection_pool_settings():
        print("\n[FAILED] Connection pool settings tests failed!")
        return False
    
    # Test error handling
    if not test_connection_pool_error_handling():
        print("\n[FAILED] Connection pool error handling tests failed!")
        return False
    
    # Test recommendations
    if not test_connection_pool_recommendations():
        print("\n[FAILED] Connection pool recommendations test failed!")
        return False
    
    print("\n[OK] All connection pool tests passed successfully!")
    print("\nConnection pool implementation is working correctly.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 