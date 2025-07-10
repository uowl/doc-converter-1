import logging
import os
import re
from urllib.parse import urlparse
from sas_url_handler import SASUrlHandler

class TriggerFileHandler:
    """Handles trigger file parsing and dynamic SAS URL management."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_trigger_file_content(self, content):
        """
        Parse trigger file content to extract source and destination SAS URLs.
        
        Expected format:
        source_sas_url:<source_sas_url>
        dest_sas_url:<dest_sas_url>
        
        Args:
            content (str): Content of the trigger file
            
        Returns:
            dict: Parsed configuration with source_sas_url and dest_sas_url
        """
        try:
            config = {}
            
            # Parse each line
            for line in content.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Look for key-value pairs
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'source_sas_url':
                        config['source_sas_url'] = value
                    elif key == 'dest_sas_url':
                        config['dest_sas_url'] = value
            
            # Validate required fields
            if 'source_sas_url' not in config:
                raise ValueError("Missing source_sas_url in trigger file")
            if 'dest_sas_url' not in config:
                raise ValueError("Missing dest_sas_url in trigger file")
            
            # Validate SAS URLs
            self._validate_sas_url(config['source_sas_url'], "source")
            self._validate_sas_url(config['dest_sas_url'], "destination")
            
            self.logger.debug(f"Successfully parsed trigger file:")
            self.logger.debug(f"  Source SAS URL: {config['source_sas_url']}")
            self.logger.debug(f"  Destination SAS URL: {config['dest_sas_url']}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error parsing trigger file content: {str(e)}")
            raise
    
    def _validate_sas_url(self, sas_url, url_type):
        """Validate a SAS URL format."""
        try:
            handler = SASUrlHandler(sas_url)
            is_valid, message = handler.validate_sas_url()
            if not is_valid:
                raise ValueError(f"Invalid {url_type} SAS URL: {message}")
            
            account_info = handler.get_account_info()
            self.logger.debug(f"{url_type.capitalize()} SAS URL validation successful:")
            self.logger.debug(f"  Container: {account_info['container_name']}")
            if account_info['additional_path']:
                self.logger.debug(f"  Additional path: {account_info['additional_path']}")
                
        except Exception as e:
            raise ValueError(f"Invalid {url_type} SAS URL: {str(e)}")
    
    def read_trigger_file(self, blob_monitor, trigger_blob_name):
        """
        Read and parse the trigger file from blob storage.
        
        Args:
            blob_monitor: BlobMonitor instance to use for downloading
            trigger_blob_name: Name of the trigger blob
            
        Returns:
            dict: Parsed configuration with source_sas_url and dest_sas_url
        """
        try:
            # Download the trigger file to a temporary location
            temp_trigger_path = os.path.join("temp", "trigger_file.txt")
            os.makedirs("temp", exist_ok=True)
            
            if not blob_monitor.download_blob(trigger_blob_name, temp_trigger_path):
                raise Exception("Failed to download trigger file")
            
            # Read the trigger file content
            with open(temp_trigger_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the content
            config = self.parse_trigger_file_content(content)
            
            # Clean up temporary file
            if os.path.exists(temp_trigger_path):
                os.remove(temp_trigger_path)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error reading trigger file {trigger_blob_name}: {str(e)}")
            raise 