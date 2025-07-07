import urllib.parse
from urllib.parse import urlparse, parse_qs, urlencode
from azure.storage.blob import BlobServiceClient

class SASUrlHandler:
    """Handles SAS URL parsing and authentication properly."""
    
    def __init__(self, sas_url):
        self.original_sas_url = sas_url
        self.parsed_url = urlparse(sas_url)
        self.account_url = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        self.container_name = self.parsed_url.path.strip('/')
        
        # Parse query parameters
        self.query_params = parse_qs(self.parsed_url.query)
        
    def get_blob_service_client(self):
        """Create a blob service client with proper SAS URL handling."""
        # Use the connection string method that works
        try:
            sas_part = self.original_sas_url.split('?')[1]
            connection_string = f"BlobEndpoint={self.account_url};SharedAccessSignature={sas_part}"
            client = BlobServiceClient.from_connection_string(connection_string)
            return client
        except Exception as e:
            print(f"Connection string method failed: {str(e)}")
            raise Exception("SAS URL authentication failed")
    
    def _reconstruct_sas_url(self):
        """Reconstruct the SAS URL with proper encoding."""
        # Get the base URL without query parameters
        base_url = f"{self.account_url}/{self.container_name}"
        
        # Reconstruct query parameters with proper encoding
        query_parts = []
        for key, values in self.query_params.items():
            for value in values:
                # Don't re-encode already encoded values
                if key in ['sig', 'sv', 'st', 'se', 'sp', 'spr', 'sip', 'sr']:
                    query_parts.append(f"{key}={value}")
                else:
                    query_parts.append(f"{key}={urllib.parse.quote(value)}")
        
        query_string = "&".join(query_parts)
        return f"{base_url}?{query_string}"
    
    def validate_sas_url(self):
        """Validate the SAS URL format and parameters."""
        required_params = ['sv', 'sig']
        optional_params = ['st', 'se', 'sp', 'spr', 'sip', 'sr']
        
        missing_required = [param for param in required_params if param not in self.query_params]
        if missing_required:
            return False, f"Missing required parameters: {missing_required}"
        
        return True, "SAS URL format is valid"
    
    def get_account_info(self):
        """Get account information from the SAS URL."""
        return {
            'account_url': self.account_url,
            'container_name': self.container_name,
            'protocol': self.parsed_url.scheme,
            'host': self.parsed_url.netloc,
            'has_required_params': all(param in self.query_params for param in ['sv', 'sig'])
        } 