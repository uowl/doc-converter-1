import os
from dotenv import load_dotenv

load_dotenv()

# Azure Blob Storage Configuration
# SAS URL can be in multiple formats:
# 1. Simple format: points directly to container
#    Example: "https://account.blob.core.windows.net/container?sp=...&sig=..."
# 2. Complex format: points to a specific folder that contains config/files/converted
#    Example: "https://account.blob.core.windows.net/container/root/folder1?sp=...&sig=..."
#    In this case, the system will look for config/, files/, and converted/ folders within root/folder1/
# 3. URL pointing to a folder named 'config'
#    Example: "https://account.blob.core.windows.net/container/root/folder1/config?sp=...&sig=..."
#    In this case, the system will look for config/, files/, and converted/ folders within root/folder1/config/

# JP SAS_URL = "https://sasstoragejp.blob.core.windows.net/mysasstorage?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=O1xmqnb8n5d%2BWRG29VFvyNDGbptS94uFa337MS5M1nc%3D"
SAS_URL = "https://sasstoragejpmain.blob.core.windows.net/main?sp=racwdl&st=2025-07-09T03:18:39Z&se=2025-07-31T11:18:39Z&spr=https&sv=2024-11-04&sr=c&sig=2%2FNpZHAoIF2IdWloD4hXmsbImRvZfKoxYSiVpUGPurk%3D"

# Azure blob storage folder structure
# These folders will be created within the container or additional path specified in SAS_URL
AZURE_CONFIG_FOLDER = "config"  # Folder in Azure blob storage for trigger files
AZURE_FILES_FOLDER = "files"    # Folder in Azure blob storage for documents to convert

# Trigger file pattern (monitored in Azure config folder)
TRIGGER_FILE_PATTERN = "start_conversion_1234.txt"

# Polling interval in seconds (2 minutes)
POLLING_INTERVAL = 120

# Supported file extensions for conversion
SUPPORTED_EXTENSIONS = {
    '.doc': 'word',
    '.docx': 'word', 
    '.txt': 'text',
    '.rtf': 'word',
    '.odt': 'word',
    '.html': 'html',
    '.htm': 'html',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.tif': 'tiff',  # TIF files will be copied as-is
    '.tiff': 'tiff', # TIFF files will be copied as-is
    '.pdf': 'pdf'  # PDF files will be copied as-is
}

# Output directory for converted files
OUTPUT_DIR = "converted_documents"

# Multi-threading configuration
ENABLE_MULTI_THREADING = True  # Set to False to disable multi-threading
MAX_WORKER_THREADS = 10  # Maximum number of concurrent conversion threads
MIN_FILES_FOR_MULTI_THREADING = 4  # Minimum files required to enable multi-threading

# Batch processing configuration
ENABLE_BATCH_PROCESSING = True  # Set to False to disable batch processing
BATCH_SIZE = 1000  # Number of files to process in each batch
BATCH_DELAY_SECONDS = 5  # Delay between batches to prevent resource exhaustion

# Connection pool configuration
CONNECTION_POOL_SIZE = 10  # Maximum number of connections in the pool
CONNECTION_POOL_MAX_RETRIES = 3  # Maximum number of retries for failed connections
CONNECTION_POOL_TIMEOUT = 30  # Connection timeout in seconds

# Progress bar configuration
ENABLE_PROGRESS_BARS = True  # Set to False to disable progress bars
PROGRESS_BAR_DESCRIPTION = "Converting documents"  # Description for progress bars
DISABLE_INDIVIDUAL_PROGRESS_BARS_IN_BATCH = True  # Disable individual progress bars during batch processing to prevent overlap
PROGRESS_BAR_LOG_DELAY = 0.1  # Delay in seconds after logging to prevent progress bar interference

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "doc_converter.log"
# Set to True to show detailed Azure SDK logs, False for clean console output
VERBOSE_AZURE_LOGS = False 