import os
from dotenv import load_dotenv

load_dotenv()

# Azure Blob Storage Configuration
SAS_URL = "https://sasstoragejp.blob.core.windows.net/mysasstorage?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=O1xmqnb8n5d%2BWRG29VFvyNDGbptS94uFa337MS5M1nc%3D"

# Trigger file pattern
TRIGGER_FILE_PATTERN = "start_converson_1234.txt"

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
    '.htm': 'html'
}

# Output directory for converted files
OUTPUT_DIR = "converted_documents"

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "doc_converter.log"
# Set to True to show detailed Azure SDK logs, False for clean console output
VERBOSE_AZURE_LOGS = False 