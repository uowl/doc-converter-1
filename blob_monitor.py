import logging
import os
from urllib.parse import urlparse, parse_qs
from azure.storage.blob import BlobServiceClient
from config import SAS_URL, TRIGGER_FILE_PATTERN, OUTPUT_DIR

class BlobMonitor:
    def __init__(self):
        self.sas_url = SAS_URL
        self.trigger_pattern = TRIGGER_FILE_PATTERN
        self.output_dir = OUTPUT_DIR
        self.processed_files = set()
        
        # Parse SAS URL to get container and account info
        parsed_url = urlparse(self.sas_url)
        self.account_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.container_name = parsed_url.path.strip('/')
        
        # Create blob service client
        self.blob_service_client = BlobServiceClient(
            account_url=self.account_url,
            credential=self.sas_url
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('doc_converter.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def check_for_trigger_file(self):
        """Check if the trigger file exists in the blob storage."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # List blobs in the container
            blobs = container_client.list_blobs()
            
            for blob in blobs:
                if blob.name == self.trigger_pattern:
                    self.logger.info(f"Trigger file found: {blob.name}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking for trigger file: {str(e)}")
            return False
    
    def get_documents_to_convert(self):
        """Get list of documents that need to be converted."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blobs = container_client.list_blobs()
            
            documents = []
            for blob in blobs:
                # Skip the trigger file and already processed files
                if blob.name == self.trigger_pattern or blob.name in self.processed_files:
                    continue
                
                # Check if it's a supported document type
                file_ext = os.path.splitext(blob.name)[1].lower()
                if file_ext in ['.doc', '.docx', '.txt', '.rtf', '.odt', '.html', '.htm']:
                    documents.append(blob.name)
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents to convert: {str(e)}")
            return []
    
    def download_blob(self, blob_name, local_path):
        """Download a blob to local storage."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            with open(local_path, "wb") as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())
            
            self.logger.info(f"Downloaded {blob_name} to {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading blob {blob_name}: {str(e)}")
            return False
    
    def upload_blob(self, local_path, blob_name):
        """Upload a file to blob storage."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            with open(local_path, "rb") as file:
                blob_client.upload_blob(file, overwrite=True)
            
            self.logger.info(f"Uploaded {local_path} as {blob_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error uploading blob {blob_name}: {str(e)}")
            return False
    
    def delete_trigger_file(self):
        """Delete the trigger file after processing."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(self.trigger_pattern)
            blob_client.delete_blob()
            self.logger.info(f"Deleted trigger file: {self.trigger_pattern}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting trigger file: {str(e)}")
            return False 