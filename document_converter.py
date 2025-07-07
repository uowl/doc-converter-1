import os
import logging
from config import SUPPORTED_EXTENSIONS, OUTPUT_DIR

class DocumentConverter:
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def convert_to_pdf(self, input_path, output_filename=None):
        """Convert a document to PDF using Aspose libraries."""
        try:
            file_ext = os.path.splitext(input_path)[1].lower()
            
            if output_filename is None:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_filename = f"{base_name}.pdf"
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            if file_ext in ['.doc', '.docx', '.rtf', '.odt']:
                return self._convert_word_document(input_path, output_path)
            elif file_ext in ['.html', '.htm']:
                return self._convert_html_document(input_path, output_path)
            elif file_ext == '.txt':
                return self._convert_text_document(input_path, output_path)
            else:
                self.logger.error(f"Unsupported file type: {file_ext}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error converting {input_path}: {str(e)}")
            return None
    
    def _convert_word_document(self, input_path, output_path):
        """Convert Word documents (DOC, DOCX, RTF, ODT) to PDF."""
        try:
            import aspose.words as aw
            
            # Load the document
            doc = aw.Document(input_path)
            
            # Save as PDF
            doc.save(output_path, aw.SaveFormat.PDF)
            
            self.logger.info(f"Converted Word document: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error converting Word document {input_path}: {str(e)}")
            return None
    
    def _convert_html_document(self, input_path, output_path):
        """Convert HTML documents to PDF."""
        try:
            import aspose.words as aw
            
            # Load the HTML document
            doc = aw.Document(input_path)
            
            # Save as PDF
            doc.save(output_path, aw.SaveFormat.PDF)
            
            self.logger.info(f"Converted HTML document: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error converting HTML document {input_path}: {str(e)}")
            return None
    
    def _convert_text_document(self, input_path, output_path):
        """Convert text documents to PDF."""
        try:
            import aspose.words as aw
            
            # Read text content
            with open(input_path, 'r', encoding='utf-8') as file:
                text_content = file.read()
            
            # Create a new document
            doc = aw.Document()
            builder = aw.DocumentBuilder(doc)
            
            # Add text content
            builder.write(text_content)
            
            # Save as PDF
            doc.save(output_path, aw.SaveFormat.PDF)
            
            self.logger.info(f"Converted text document: {input_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error converting text document {input_path}: {str(e)}")
            return None
    
    def cleanup_temp_files(self, file_path):
        """Clean up temporary files after conversion."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up file {file_path}: {str(e)}") 