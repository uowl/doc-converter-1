# Changelog

## [1.1.0] - 2024-01-XX

### Added
- **SAS URL Path Support**: Added support for SAS URLs with embedded folder paths
  - Simple format: `https://account.blob.core.windows.net/container?sp=...&sig=...`
  - Complex format: `https://account.blob.core.windows.net/container/root/folder1/config?sp=...&sig=...`
- **Automatic Path Detection**: System automatically detects URL format and adjusts folder paths
- **Backward Compatibility**: Existing simple container URLs continue to work without changes
- **Enhanced SAS URL Handler**: Improved parsing and validation of SAS URLs with additional paths
- **Test Scripts**: Added comprehensive test scripts for SAS URL path parsing
- **Documentation**: Updated README with examples and usage instructions

### Changed
- **SASUrlHandler**: Enhanced to parse container name and additional path components
- **BlobMonitor**: Updated to work with additional path information from SAS URL
- **Main Application**: Modified to handle path construction for converted file uploads
- **Configuration**: Added comments explaining the two SAS URL formats

### Technical Details
- **Path Parsing**: Extracts container name and additional path from SAS URL
- **Folder Construction**: Automatically builds correct paths for config, files, and converted folders
- **Error Handling**: Improved validation and error reporting for malformed URLs
- **Logging**: Enhanced logging to show container and path information

### Files Modified
- `sas_url_handler.py` - Enhanced SAS URL parsing
- `blob_monitor.py` - Updated to handle additional paths
- `main.py` - Modified upload path construction
- `config.py` - Added documentation comments
- `README.md` - Added comprehensive documentation
- `test_sas_url_paths.py` - New test script
- `example_sas_urls.py` - New example script

### Files Added
- `test_sas_url_paths.py` - Test script for SAS URL path parsing
- `example_sas_urls.py` - Example script demonstrating different URL formats
- `CHANGELOG.md` - This changelog file

### Migration Guide
No migration required for existing users. The system automatically detects the URL format:
- **Existing users**: Continue using simple container URLs as before
- **New users**: Can use either simple or complex URL formats
- **Configuration**: No changes needed to existing configuration files

### Examples

#### Simple Container URL (Existing Format)
```
SAS_URL = "https://account.blob.core.windows.net/container?sp=racwdl&sig=..."
```
Folder structure:
```
container/
├── config/start_converson_1234.txt
├── files/document1.docx
└── converted/document1.pdf
```

#### URL Pointing to Specific Folder (New Format)
```
SAS_URL = "https://account.blob.core.windows.net/container/root/folder1?sp=racwdl&sig=..."
```
Folder structure:
```
container/
└── root/
    └── folder1/
        ├── config/start_converson_1234.txt
        ├── files/document1.docx
        └── converted/document1.pdf
```

#### URL Pointing to Folder Named 'config' (New Format)
```
SAS_URL = "https://account.blob.core.windows.net/container/root/folder1/config?sp=racwdl&sig=..."
```
Folder structure:
```
container/
└── root/
    └── folder1/
        └── config/
            ├── config/start_converson_1234.txt
            ├── files/document1.docx
            └── converted/document1.pdf
```

### Testing
Run the test scripts to verify functionality:
```bash
python test_sas_url_paths.py
python example_sas_urls.py
``` 