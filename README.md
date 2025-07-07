# Document Converter Application

A Python application that monitors Azure Blob Storage for a trigger file and converts documents to PDF using Aspose libraries. This application simulates Azure Functions blob trigger functionality but runs locally.

## Features

- **Blob Storage Monitoring**: Continuously monitors Azure Blob Storage for a specific trigger file
- **Document Conversion**: Converts various document formats to PDF using Aspose libraries
- **Supported Formats**: DOC, DOCX, TXT, RTF, ODT, HTML, HTM
- **Automatic Processing**: Downloads documents, converts them, and uploads the PDFs back to blob storage
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

## Configuration

Edit `config.py` to customize the application:

```python
# Azure Blob Storage Configuration
SAS_URL = "your-sas-url-here"

# Trigger file pattern
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
    '.htm': 'html'
}
```

## Usage

### Running the Application

1. **Start the application:**
   ```bash
   python main.py
   ```

2. **Upload documents to blob storage:**
   - Upload documents you want to convert to your blob container
   - Supported formats: DOC, DOCX, TXT, RTF, ODT, HTML, HTM

3. **Trigger conversion:**
   - Upload a file named `start_converson_1234.txt` to the blob container
   - The application will detect this trigger file and start processing

4. **Monitor the process:**
   - Check the console output and `doc_converter.log` for progress
   - Converted PDFs will be uploaded to the `converted/` folder in blob storage

### How It Works

1. **Monitoring**: The application polls the blob storage every 2 minutes (configurable)
2. **Trigger Detection**: When `start_converson_1234.txt` is found, processing begins
3. **Document Discovery**: All supported documents in the container are identified
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

| Format | Extension | Conversion Method |
|--------|-----------|-------------------|
| Microsoft Word | .doc, .docx | Aspose.Words |
| Rich Text Format | .rtf | Aspose.Words |
| OpenDocument Text | .odt | Aspose.Words |
| Plain Text | .txt | Aspose.Words |
| HTML | .html, .htm | Aspose.Words |

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