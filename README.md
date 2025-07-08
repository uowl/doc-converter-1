# Document Converter Application

A Python application that monitors Azure Blob Storage for a trigger file and converts documents to PDF using Aspose libraries. This application simulates Azure Functions blob trigger functionality but runs locally.

## Features

- **Azure Blob Storage Monitoring**: Continuously monitors Azure Blob Storage for a specific trigger file in a `config` folder
- **Document Conversion**: Converts various document formats to PDF using Aspose libraries
- **Supported Formats**: DOC, DOCX, TXT, RTF, ODT, HTML, HTM, JPG, PNG, TIF, PDF
- **PDF/TIF Handling**: PDF and TIF files are copied as-is without conversion
- **Image Conversion**: JPG and PNG images are converted to PDF format
- **Automatic Processing**: Downloads documents from `files` folder, converts them, and uploads the PDFs back to blob storage
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

```python
# Azure Blob Storage Configuration
SAS_URL = "your-sas-url-here"

# Azure blob storage folder structure
AZURE_CONFIG_FOLDER = "config"  # Folder for trigger files
AZURE_FILES_FOLDER = "files"    # Folder for documents to convert

# Trigger file pattern (monitored in Azure config folder)
TRIGGER_FILE_PATTERN = "start_converson_1234.txt"

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

## File Structure

```
doc-converter/
├── main.py                 # Main application entry point
├── blob_monitor.py         # Blob storage monitoring and operations
├── document_converter.py   # Document conversion using Aspose
├── failed_conversions.py   # Failed conversion tracking and CSV management
├── view_failures.py        # Utility to view and manage failed conversions
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

- **Polling Interval**: Adjust `POLLING_INTERVAL` in `config.py` based on your needs (currently set to 2 minutes)
- **Batch Processing**: All documents are processed when the trigger file is detected
- **Memory Usage**: Documents are processed one at a time to manage memory usage

## License

This application uses Aspose libraries which require a license for production use. For evaluation purposes, Aspose provides a free trial.

## Support

For issues related to:
- **Aspose Libraries**: Contact Aspose support
- **Azure Blob Storage**: Check Azure documentation
- **Application Logic**: Review logs and configuration 