# Document Converter Application

A Python application that monitors Azure Blob Storage for a trigger file and converts documents to PDF using Aspose libraries. This application simulates Azure Functions blob trigger functionality but runs locally.

## Features

- **Azure Blob Storage Monitoring**: Continuously monitors Azure Blob Storage for a specific trigger file in a `config` folder
- **Multi-Threaded Document Conversion**: Processes multiple documents concurrently using configurable thread pools
- **Batch Processing**: Processes large document sets in manageable batches to prevent memory issues
- **Document Conversion**: Converts various document formats to PDF using Aspose libraries
- **Supported Formats**: DOC, DOCX, TXT, RTF, ODT, HTML, HTM, JPG, PNG, TIF, PDF
- **PDF/TIF Handling**: PDF and TIF files are copied as-is without conversion
- **Image Conversion**: JPG and PNG images are converted to PDF format
- **Automatic Processing**: Downloads documents from `files` folder, converts them, and uploads the PDFs back to blob storage
- **Thread-Safe Operations**: Thread-safe logging, error handling, and resource management
- **Progress Bars**: Visual progress tracking for document conversion with real-time updates
- **Resource Management**: Automatic memory cleanup and batch delays to prevent system overload
- **Logging**: Comprehensive logging for monitoring and debugging

## Prerequisites

- Python 3.7 or higher
- Azure Blob Storage account with SAS URL access
- Aspose license (for production use)

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd doc-converter
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**
   - The SAS URL is already configured in `config.py`
   - Modify settings in `config.py` if needed

## Azure Blob Storage Structure

The application expects the following folder structure in your Azure blob container:

```
your-blob-container/
├── config/                    # Folder for trigger files
│   └── start_converson_1234.txt  # Trigger file (any .txt file)
├── files/                     # Folder for documents to convert
│   ├── document1.docx
│   ├── document2.txt
│   └── document3.html
└── converted/                 # Output folder for converted PDFs (created automatically)
    ├── document1.pdf
    ├── document2.pdf
    └── document3.pdf
```

## Configuration

Edit `config.py` to customize the application:

### Multi-Threading Configuration

The application supports multi-threaded document processing for improved performance:

```python
# Multi-threading configuration
ENABLE_MULTI_THREADING = True  # Set to False to disable multi-threading
MAX_WORKER_THREADS = 4  # Maximum number of concurrent conversion threads
MIN_FILES_FOR_MULTI_THREADING = 4  # Minimum files required to enable multi-threading
```

**Multi-threading behavior:**
- **Enabled by default**: Multi-threading is enabled when `ENABLE_MULTI_THREADING = True`
- **Minimum file threshold**: Multi-threading only activates when processing 4 or more files (configurable via `MIN_FILES_FOR_MULTI_THREADING`)
- **Thread count**: Uses up to 16 concurrent threads (configurable via `MAX_WORKER_THREADS`)
- **Thread safety**: All operations are thread-safe with proper synchronization
- **Fallback**: Automatically falls back to sequential processing for fewer files or when disabled

**Performance benefits:**
- **Concurrent processing**: Multiple documents are converted simultaneously
- **Reduced total time**: Significantly faster processing for large batches
- **Resource efficiency**: Optimal use of CPU cores and network bandwidth
- **Thread isolation**: Each thread has its own document converter instance

### Batch Processing Configuration

The application supports batch processing for large document sets:

```python
# Batch processing configuration
ENABLE_BATCH_PROCESSING = True  # Set to False to disable batch processing
BATCH_SIZE = 1000  # Number of files to process in each batch
BATCH_DELAY_SECONDS = 5  # Delay between batches to prevent resource exhaustion
```

**Batch processing features:**
- **Memory management**: Processes documents in manageable chunks to prevent memory issues
- **Resource cleanup**: Automatic cleanup between batches to free system resources
- **Progress tracking**: Overall progress bar showing completion across all batches
- **Batch delays**: Configurable delays between batches to prevent system overload
- **Error isolation**: Failures in one batch don't affect subsequent batches
- **Processing estimates**: Automatic time and resource usage estimates
- **Configuration validation**: Automatic validation of batch settings

### Connection Pool Configuration

The application uses connection pooling to optimize Azure Blob Storage operations:

```python
# Connection pool configuration
CONNECTION_POOL_SIZE = 50  # Maximum number of connections in the pool
CONNECTION_POOL_MAX_RETRIES = 3  # Maximum number of retries for failed connections
CONNECTION_POOL_TIMEOUT = 30  # Connection timeout in seconds
```

**Connection pool features:**
- **Connection reuse**: Reuses HTTP connections to reduce latency
- **Concurrent operations**: Supports multiple simultaneous blob operations
- **Automatic retries**: Handles transient network failures gracefully
- **Timeout management**: Prevents hanging connections
- **Resource optimization**: Reduces memory and CPU usage for network operations

### Progress Bar Configuration

The application includes visual progress tracking for document conversion:

```python
# Progress bar configuration
ENABLE_PROGRESS_BARS = True  # Set to False to disable progress bars
PROGRESS_BAR_DESCRIPTION = "Converting documents"  # Description for progress bars
```

**Progress bar features:**
- **Real-time updates**: Shows current file being processed
- **Progress tracking**: Displays completed/total documents
- **Time estimates**: Shows elapsed time and estimated remaining time
- **Processing rate**: Displays documents processed per second
- **Thread-safe**: Works correctly with multi-threaded processing
- **Fallback support**: Gracefully handles missing tqdm library

```python
# Azure Blob Storage Configuration
# SAS URL can be in two formats:
# 1. Simple format: points directly to container
#    Example: "https://account.blob.core.windows.net/container?sp=...&sig=..."
# 2. Complex format: includes additional path after container
#    Example: "https://account.blob.core.windows.net/container/root/folder1/config?sp=...&sig=..."
#    In this case, the system will look for config/ and files/ folders within the additional path
SAS_URL = "your-sas-url-here"

# Azure blob storage folder structure
# These folders will be created within the container or additional path specified in SAS_URL
AZURE_CONFIG_FOLDER = "config"  # Folder for trigger files
AZURE_FILES_FOLDER = "files"    # Folder for documents to convert

# Trigger file pattern (monitored in Azure config folder)
TRIGGER_FILE_PATTERN = "start_conversion_1234.txt"

# Polling interval in seconds (2 minutes)
POLLING_INTERVAL = 120

# Supported file extensions
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
```

## Usage

### Running the Application

1. **Start the application:**
   ```bash
   python main.py
   ```

2. **Upload documents to Azure blob storage:**
   - Upload documents you want to convert to the `files/` folder in your blob container
   - Supported formats: DOC, DOCX, TXT, RTF, ODT, HTML, HTM, JPG, PNG, TIF, PDF

3. **Trigger conversion:**
   - Upload a file named `start_converson_1234.txt` to the `config/` folder in your blob container
   - The application will detect this trigger file and start processing

4. **Monitor the process:**
   - Check the console output and `doc_converter.log` for progress
   - Converted PDFs will be uploaded to the `converted/` folder in blob storage

### How It Works

1. **Monitoring**: The application polls the Azure blob storage every 2 minutes (configurable)
2. **Trigger Detection**: When `config/start_converson_1234.txt` is found, processing begins
3. **Document Discovery**: All supported documents in the `files/` folder are identified
4. **Download**: Documents are downloaded to a temporary local directory
5. **Conversion**: Each document is converted to PDF using Aspose libraries
6. **Upload**: Converted PDFs are uploaded to the `converted/` folder in blob storage
7. **Cleanup**: Temporary files are removed and the trigger file is deleted

## SAS URL Format Support

The application supports two SAS URL formats:

### 1. Simple Container URL
```
https://account.blob.core.windows.net/container?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=...
```

**Folder Structure:**
```
container/
├── config/                 # Trigger files
│   └── start_converson_1234.txt
├── files/                  # Documents to convert
│   ├── document1.docx
│   └── document2.pdf
└── converted/              # Output folder (created automatically)
    ├── document1.pdf
    └── document2.pdf
```

### 2. Complex URL with Additional Path
```
https://account.blob.core.windows.net/container/root/folder1?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=...
```

**Folder Structure:**
```
container/
└── root/
    └── folder1/           # Additional path from URL
        ├── config/        # Trigger files
        │   └── start_converson_1234.txt
        ├── files/         # Documents to convert
        │   ├── document1.docx
        │   └── document2.pdf
        └── converted/     # Output folder (created automatically)
            ├── document1.pdf
            └── document2.pdf
```

### 3. URL Pointing to Folder Named 'config'
```
https://account.blob.core.windows.net/container/root/folder1/config?sp=racwdl&st=2025-07-07T04:28:44Z&se=2025-07-31T12:28:44Z&sip=108.49.61.242&sv=2024-11-04&sr=c&sig=...
```

**Folder Structure:**
```
container/
└── root/
    └── folder1/
        └── config/        # Additional path from URL
            ├── config/    # Trigger files
            │   └── start_converson_1234.txt
            ├── files/     # Documents to convert
            │   ├── document1.docx
            │   └── document2.pdf
            └── converted/ # Output folder (created automatically)
                ├── document1.pdf
                └── document2.pdf
```

The system automatically detects the URL format and adjusts the folder paths accordingly.

## Dynamic SAS URL Support

The application now supports dynamic SAS URL configuration through trigger files. This allows you to specify different source and destination SAS URLs for each job.

### Trigger File Format

Create a trigger file with the following content:

```
source_sas_url:https://account.blob.core.windows.net/source-container/source-path?sp=...&sv=...&sig=...
dest_sas_url:https://account.blob.core.windows.net/dest-container/dest-path?sp=...&sv=...&sig=...
```

### Folder Structure for Dynamic SAS URLs

**MAIN SAS URL** (used only for trigger file monitoring):
```
main-container/
└── main-path/
    └── config/
        └── start_conversion_1234.txt  (trigger file)
```

**SOURCE SAS URL** (used only for reading files):
```
source-container/
└── source-path/
    └── files/
        ├── document1.docx
        └── document2.pdf
```

**DESTINATION SAS URL** (used only for uploading converted files):
```
dest-container/
└── dest-path/
    └── converted/
        ├── document1.pdf
        └── document2.pdf
```

### How Dynamic SAS URLs Work

1. **Main SAS URL**: The application starts with a main SAS URL that monitors the `config/` folder for trigger files
2. **Trigger File**: When a trigger file is detected, the application reads the `source_sas_url` and `dest_sas_url` from the file
3. **Source Operations**: Files are downloaded from the `files/` folder in the source SAS URL container
4. **Destination Operations**: Converted files are uploaded to the `converted/` folder in the destination SAS URL container
5. **Job Status**: Log files are uploaded to the `job_status/` folder in the main SAS URL container

### Example Usage

1. **Upload trigger file** to your main SAS URL's `config/` folder:
   ```
   config/start_conversion_1234.txt
   ```

2. **Content of trigger file**:
   ```
   source_sas_url:https://account.blob.core.windows.net/source-container/source-path?sp=racwdl&sv=2024-11-04&sig=...
   dest_sas_url:https://account.blob.core.windows.net/dest-container/dest-path?sp=racwdl&sv=2024-11-04&sig=...
   ```

3. **The application will**:
   - Read files from `source-container/source-path/files/`
   - Convert documents to PDF
   - Upload converted files to `dest-container/dest-path/converted/`
   - Upload job log to `main-container/main-path/job_status/job_YYYYMMDD_HHMMSS.log`

## Job Status Logging

After each job completes (success or failure), the application automatically uploads the log file to the main SAS URL's `job_status/` folder with a timestamped filename.

### Log File Location

- **Local**: `doc_converter.log` (configurable via `LOG_FILE` in `config.py`)
- **Remote**: `job_status/job_YYYYMMDD_HHMMSS.log` in the main SAS URL container

### Log Format

The application uses consistent logging indicators:
- `[OK]` for success messages
- `[FAILED]` for failure messages

Example log entries:
```
[OK] Successfully converted and uploaded: document1.docx
[FAILED] Failed to download document2.pdf from source
[OK] Uploaded job log to job_status/job_20240115_143022.log in main SAS URL container.
```

## File Structure

```
doc-converter/
├── main.py                 # Main application entry point
├── multi_thread_processor.py # Multi-threaded document processing
├── batch_processor.py      # Batch processing for large document sets
├── blob_monitor.py         # Blob storage monitoring and operations
├── document_converter.py   # Document conversion using Aspose
├── failed_conversions.py   # Failed conversion tracking and CSV management
├── view_failures.py        # Utility to view and manage failed conversions
├── sas_url_handler.py     # SAS URL parsing and authentication
├── test_sas_url_paths.py  # Test script for SAS URL path parsing
├── test_multi_threading.py # Test script for multi-threading functionality
├── config.py              # Configuration settings
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── converted_documents/    # Local output directory (created automatically)
├── temp/                  # Temporary files (created automatically)
├── doc_converter.log      # Application logs (created automatically)
└── failed_conversions.csv # Failed conversion records (created automatically)
```

## Supported Document Formats

| Format | Extension | Processing Method |
|--------|-----------|-------------------|
| Microsoft Word | .doc, .docx | Convert to PDF |
| Rich Text Format | .rtf | Convert to PDF |
| OpenDocument Text | .odt | Convert to PDF |
| Plain Text | .txt | Convert to PDF |
| HTML | .html, .htm | Convert to PDF |
| JPEG Images | .jpg, .jpeg | Convert to PDF |
| PNG Images | .png | Convert to PDF |
| TIFF Images | .tif, .tiff | Copy as-is |
| PDF Documents | .pdf | Copy as-is |

## Logging

The application provides comprehensive logging:

- **Console Output**: Real-time status updates
- **Log File**: `doc_converter.log` with detailed information
- **Log Levels**: INFO, ERROR, DEBUG

## Error Handling

The application includes robust error handling:

- **Network Issues**: Retries and graceful handling of blob storage connectivity
- **Conversion Errors**: Individual document failures don't stop the entire process
- **File System**: Proper cleanup of temporary files
- **Authentication**: SAS URL validation and error reporting
- **Failed Conversion Tracking**: Comprehensive CSV-based tracking of all failed conversions

### Failed Conversion Tracking

The application maintains a `failed_conversions.csv` file that records all failed conversions with:

- **Timestamp**: When the failure occurred
- **Filename**: The document that failed to convert
- **File Size**: Size of the file in bytes
- **Error Type**: Categorized error types (DOWNLOAD_FAILED, CONVERSION_FAILED, UPLOAD_FAILED, PROCESSING_ERROR)
- **Error Message**: Detailed error description
- **Attempt Count**: Number of attempts made

#### Viewing Failed Conversions

Use the utility script to view and manage failed conversions:

```bash
# View summary of all failures
python view_failures.py summary

# List recent failures (last 24 hours)
python view_failures.py list

# List failures with filters
python view_failures.py list --error-type CONVERSION_FAILED --hours 48

# Export failures to a new CSV file
python view_failures.py export --output my_failures.csv

# Clear old records (older than 30 days)
python view_failures.py clear --days 30
```

## Troubleshooting

### Common Issues

1. **SAS URL Expired**: Update the SAS URL in `config.py`
2. **Network Connectivity**: Check internet connection and firewall settings
3. **Aspose License**: Ensure you have a valid Aspose license for production use
4. **File Permissions**: Ensure the application has write permissions for temp and output directories
5. **Azure Folder Structure**: Ensure your blob container has the correct folder structure (`config/` and `files/` folders)

### Debug Mode

To enable debug logging, modify the logging level in `config.py`:

```python
LOG_LEVEL = "DEBUG"
```

## Security Considerations

- **SAS URL**: Keep your SAS URL secure and rotate it regularly
- **Local Storage**: Temporary files are stored locally and cleaned up automatically
- **Network**: Ensure secure network connectivity to Azure Blob Storage

## Performance

- **Multi-Threaded Processing**: Up to 16 documents can be processed concurrently (configurable)
- **Batch Processing**: Large document sets processed in manageable chunks (default 1000 files per batch)
- **Thread Pool Management**: Automatic thread pool creation and cleanup for optimal resource usage
- **Thread-Safe Operations**: All shared resources are properly synchronized
- **Performance Monitoring**: Processing time and thread usage statistics are logged
- **Progress Tracking**: Visual progress bars with real-time updates and time estimates
- **Resource Management**: Automatic memory cleanup and batch delays to prevent system overload
- **Polling Interval**: Adjust `POLLING_INTERVAL` in `config.py` based on your needs (currently set to 2 minutes)
- **Batch Processing**: All documents are processed when the trigger file is detected
- **Memory Usage**: Documents are processed with thread-local storage to manage memory usage

## License

This application uses Aspose libraries which require a license for production use. For evaluation purposes, Aspose provides a free trial.

## Support

For issues related to:
- **Aspose Libraries**: Contact Aspose support
- **Azure Blob Storage**: Check Azure documentation
- **Application Logic**: Review logs and configuration 