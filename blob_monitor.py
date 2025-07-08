import logging
import os
from urllib.parse import urlparse, parse_qs
from azure.storage.blob import BlobServiceClient
from config import SAS_URL, TRIGGER_FILE_PATTERN, OUTPUT_DIR, AZURE_CONFIG_FOLDER, AZURE_FILES_FOLDER
from sas_url_handler import SASUrlHandler

class BlobMonitor:
    def __init__(self):
        self.sas_url = SAS_URL
        self.trigger_pattern = TRIGGER_FILE_PATTERN
        self.output_dir = OUTPUT_DIR
        self.azure_config_folder = AZURE_CONFIG_FOLDER
        self.azure_files_folder = AZURE_FILES_FOLDER
        self.processed_files = set()
        
        # Use the SAS URL handler for proper authentication
        self.sas_handler = SASUrlHandler(self.sas_url)
        
        # Validate SAS URL
        is_valid, message = self.sas_handler.validate_sas_url()
        if not is_valid:
            raise Exception(f"SAS URL validation failed: {message}")
        
        # Get account info
        account_info = self.sas_handler.get_account_info()
        self.account_url = account_info['account_url']
        self.container_name = account_info['container_name']
        
        # Create blob service client using the handler
        self.blob_service_client = self.sas_handler.get_blob_service_client()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup logging with reduced Azure SDK verbosity
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('doc_converter.log'),
                logging.StreamHandler()
            ]
        )
        
        # Reduce Azure SDK logging verbosity based on configuration
        from config import VERBOSE_AZURE_LOGS
        if not VERBOSE_AZURE_LOGS:
            logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
            logging.getLogger('azure.storage.blob').setLevel(logging.WARNING)
            logging.getLogger('azure.core.pipeline').setLevel(logging.WARNING)
            logging.getLogger('azure.core.pipeline.transport').setLevel(logging.WARNING)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"BlobMonitor initialized")
        self.logger.info(f"Azure config folder: {self.azure_config_folder}")
        self.logger.info(f"Azure files folder: {self.azure_files_folder}")
        self.logger.info(f"Trigger file: {self.trigger_pattern}")
    
    def check_for_trigger_file(self):
        """Check if the trigger file exists in the Azure config folder."""
        try:
            self.logger.info(f"Checking Azure config folder for trigger file: {self.trigger_pattern}")
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # List blobs in the config folder
            blobs = container_client.list_blobs(name_starts_with=f"{self.azure_config_folder}/")
            
            for blob in blobs:
                # Check if the blob name matches the trigger pattern in the config folder
                if blob.name == f"{self.azure_config_folder}/{self.trigger_pattern}":
                    self.logger.info(f"Trigger file found in Azure config folder: {blob.name}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking for trigger file in Azure config folder: {str(e)}")
            self.logger.error(f"Account URL: {self.account_url}")
            self.logger.error(f"Container: {self.container_name}")
            return False
    
    def get_documents_to_convert(self):
        """Get list of documents that need to be converted from Azure files folder."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            # List blobs in the files folder
            blobs = container_client.list_blobs(name_starts_with=f"{self.azure_files_folder}/")
            
            documents = []
            for blob in blobs:
                # Skip the folder itself and already processed files
                if blob.name == f"{self.azure_files_folder}/" or blob.name in self.processed_files:
                    continue
                
                # Get just the filename without the folder prefix
                filename = blob.name.replace(f"{self.azure_files_folder}/", "")
                
                # Check if it's a supported document type
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in ['.doc', '.docx', '.txt', '.rtf', '.odt', '.html', '.htm', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.pdf']:
                    documents.append(blob.name)  # Use full blob path for download
            
            self.logger.info(f"Found {len(documents)} documents to convert in Azure files folder")
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents to convert from Azure files folder: {str(e)}")
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
        """Delete the trigger file from Azure config folder after processing."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            trigger_blob_name = f"{self.azure_config_folder}/{self.trigger_pattern}"
            blob_client = container_client.get_blob_client(trigger_blob_name)
            blob_client.delete_blob()
            self.logger.info(f"Deleted trigger file from Azure config folder: {trigger_blob_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting trigger file from Azure config folder: {str(e)}")
            return False 