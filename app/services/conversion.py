import os
import logging
import time
from typing import Dict, Tuple, Optional
import xml.etree.ElementTree as ET
import html
import tempfile
import shutil
import base64
from urllib.parse import urlparse
from app.core.config import settings
from app.utils.formula_converter import formula_converter

# For a real implementation, additional imports would be needed for proper EPUB and MOBI conversion

logger = logging.getLogger(__name__)


class EbookConverter:
    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.output_dir = settings.OUTPUT_DIR
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    def convert(self) -> Dict[str, str]:
        """
        Convert XML to various formats (HTML, EPUB, MOBI)
        Returns dict with paths to converted files
        """
        result_paths = {}
        
        try:
            # Convert to HTML
            html_path = self._convert_to_html()
            if html_path:
                result_paths["html"] = html_path
            
            # Convert to EPUB
            epub_path = self._convert_to_epub()
            if epub_path:
                result_paths["epub"] = epub_path
            
            # Convert to MOBI
            mobi_path = self._convert_to_mobi()
            if mobi_path:
                result_paths["mobi"] = mobi_path
                
            return result_paths
            
        except Exception as e:
            logger.error(f"Error converting XML: {str(e)}")
            raise
    
    def _convert_to_html(self) -> Optional[str]:
        """
        Convert XML to HTML
        Returns path to HTML file or None if conversion failed
        """
        try:
            # Parse XML file
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            
            # Create HTML content
            html_content = []
            html_content.append("<!DOCTYPE html>")
            html_content.append("<html lang='en'>")
            html_content.append("<head>")
            html_content.append("  <meta charset='UTF-8'>")
            html_content.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
            
            # Get book title from filename
            title = os.path.basename(self.xml_path).split('.')[0]
            html_content.append(f"  <title>{title}</title>")
            html_content.append("  <style>")
            html_content.append("    body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }")
            html_content.append("    h1 { text-align: center; }")
            html_content.append("    .metadata { background-color: #f0f0f0; padding: 10px; margin-bottom: 20px; }")
            html_content.append("    .page { border-bottom: 1px solid #ccc; padding-bottom: 10px; margin-bottom: 20px; }")
            html_content.append("    .formula { background-color: #f8f8f8; font-family: monospace; padding: 5px; }")
            html_content.append("  </style>")
            html_content.append("</head>")
            html_content.append("<body>")
            html_content.append(f"  <h1>{title}</h1>")
            
            # Add metadata
            metadata = root.find("metadata")
            if metadata is not None:
                html_content.append("  <div class='metadata'>")
                html_content.append("    <h2>Metadata</h2>")
                
                for child in metadata:
                    if child.tag != "ddt":
                        html_content.append(f"    <p><strong>{child.tag}:</strong> {child.text}</p>")
                
                # Add date/time
                ddt = metadata.find("ddt")
                if ddt is not None:
                    html_content.append(f"    <p><strong>Date/Time:</strong> {ddt.text}</p>")
                
                html_content.append("  </div>")
            
            # Add content
            content = root.find("content")
            if content is not None:
                html_content.append("  <div class='content'>")
                
                # Add text
                text_section = content.find("text")
                if text_section is not None:
                    for page in text_section.findall("*"):
                        html_content.append(f"  <div class='page' id='{page.get('id', '')}'>")
                        html_content.append(f"    <h3>Page/Section {page.get('id', '')}</h3>")
                        if page.text:
                            html_content.append(f"    <p>{html.escape(page.text)}</p>")
                        html_content.append("  </div>")
                
                # Add images
                images_section = content.find("images")
                if images_section is not None:
                    logger.info(f"Found images section with {len(images_section)} child elements")
                    html_content.append("  <div class='images'>")
                    html_content.append("    <h3>Images</h3>")
                    for graphic_node in images_section.findall("{http://www.tei-c.org/ns/1.0}graphic"):
                        src_url = graphic_node.get("{http://www.w3.org/1999/xlink}href", "")
                        logger.info(f"Processing image with src_url: {src_url}")
                        if src_url:
                            try:
                                # Clean up the image path
                                clean_path = src_url
                                if clean_path.startswith("http://localhost:8000/static/"):
                                    clean_path = clean_path.replace("http://localhost:8000/static/", "")
                                elif clean_path.startswith("static/"):
                                    clean_path = clean_path.replace("static/", "")
                                elif clean_path.startswith("/static/"):
                                    clean_path = clean_path.replace("/static/", "")
                                
                                # Remove any remaining leading slashes
                                clean_path = clean_path.lstrip('/')
                                
                                # Get just the filename for better path resolution
                                img_filename = os.path.basename(clean_path)
                                
                                # Try multiple possible image locations with enhanced path resolution
                                possible_paths = [
                                    # Direct path if it exists
                                    clean_path if os.path.isabs(clean_path) else None,
                                    
                                    # Project root + static + clean_path
                                    os.path.join(self.project_root, 'static', clean_path),
                                    
                                    # Project root + static + extracted_images + filename
                                    os.path.join(self.project_root, 'static', 'extracted_images', img_filename),
                                    
                                    # Settings static dir + clean_path
                                    os.path.join(settings.STATIC_DIR, clean_path),
                                    
                                    # Settings static dir + extracted_images + filename
                                    os.path.join(settings.STATIC_DIR, 'extracted_images', img_filename),
                                    
                                    # Current working directory + static + extracted_images + filename
                                    os.path.join(os.getcwd(), 'static', 'extracted_images', img_filename),
                                    
                                    # Backend directory + static + extracted_images + filename
                                    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'extracted_images', img_filename),
                                    
                                    # Legacy paths for backward compatibility
                                    os.path.join(self.project_root, 'extracted_images', img_filename),
                                ]
                                
                                # Filter out None values and duplicates
                                possible_paths = list(dict.fromkeys([p for p in possible_paths if p is not None]))
                                
                                abs_image_path = None
                                for j, path in enumerate(possible_paths):
                                    logger.debug(f"Trying image path {j+1}: {path}")
                                    if os.path.exists(path) and os.path.isfile(path):
                                        abs_image_path = path
                                        logger.info(f"✓ Found image at path {j+1}: {path}")
                                        break
                                
                                if abs_image_path and os.path.exists(abs_image_path):
                                    # Embed the image as Base64 data
                                    logger.info(f"Embedding image as Base64: {abs_image_path}")
                                    with open(abs_image_path, "rb") as image_file:
                                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                                        ext = os.path.splitext(abs_image_path)[1].lower().lstrip('.')
                                        if ext == 'jpg':
                                            ext = 'jpeg'
                                        elif ext not in ['png', 'jpeg', 'gif', 'webp', 'svg']:
                                            ext = 'png'  # Default fallback
                                        data_uri = f"data:image/{ext};base64,{encoded_string}"
                                        html_content.append(f'''
                                            <div style="margin: 15px 0; text-align: center;">
                                                <img src="{data_uri}" alt="Extracted Image" 
                                                     style="max-width: 100%; max-height: 600px; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                                <p style="font-size: 12px; color: #666; margin-top: 5px;">{img_filename}</p>
                                            </div>
                                        ''')
                                        logger.info(f"✓ Successfully embedded image: {img_filename} (size: {len(encoded_string)} chars)")
                                else:
                                    logger.warning(f"❌ Image not found in any location: {img_filename}")
                                    logger.warning(f"Original URL: {src_url}")
                                    logger.warning(f"Searched {len(possible_paths)} locations")
                                    
                                    # List existing files in the expected directory for debugging
                                    expected_dir = os.path.join(self.project_root, "static", "extracted_images")
                                    if os.path.exists(expected_dir):
                                        existing_files = os.listdir(expected_dir)
                                        logger.warning(f"Files in {expected_dir}: {existing_files[:5]}...")
                                    
                                    html_content.append(f'''
                                        <div style="margin: 15px 0; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">
                                            <p style="color: #856404; margin: 0;">⚠️ Image not found: {img_filename}</p>
                                            <p style="font-size: 10px; color: #856404; margin: 5px 0 0 0;">Original URL: {src_url}</p>
                                        </div>
                                    ''')
                            except Exception as e:
                                logger.error(f"Failed to embed image {src_url}: {e}")
                                html_content.append(f'''
                                    <div style="margin: 15px 0; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">
                                        <p style="color: #721c24; margin: 0;">❌ Error processing image: {os.path.basename(src_url)}</p>
                                    </div>
                                ''')
                    html_content.append("  </div>")
                else:
                    logger.warning("No images section found in XML content")
                
                # Add formulas
                formulas_section = content.find("formulas")
                if formulas_section is not None:
                    html_content.append("  <div class='formulas'>")
                    html_content.append("    <h3>Formulas</h3>")
                    for formula in formulas_section.findall("formula"):
                        readable_formula = formula_converter.convert_to_readable(formula.text or "")
                        html_content.append(f"    <div class='formula'>{readable_formula}</div>")
                    html_content.append("  </div>")
                
                html_content.append("  </div>")
            
            html_content.append("</body>")
            html_content.append("</html>")
            
            # Save HTML to file
            html_path = os.path.join(self.output_dir, os.path.basename(self.xml_path).split('.')[0] + ".html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(html_content))
            
            return html_path
            
        except Exception as e:
            logger.error(f"Error converting to HTML: {str(e)}")
            return None
    
    def _convert_to_epub(self) -> Optional[str]:
        """
        Convert XML to EPUB
        Returns path to EPUB file or None if conversion failed
        
        Note: In a real implementation, this would use a proper EPUB library
        like ebooklib to create a valid EPUB file with proper structure.
        This is a simplified example.
        """
        try:
            # In a real implementation, this would convert XML to EPUB using ebooklib
            # For this demo, we'll create a simple EPUB-like file
            
            # Start with HTML conversion
            html_path = self._convert_to_html()
            if not html_path:
                return None
            
            # Create a simple EPUB-like file (not a real EPUB)
            epub_path = os.path.join(self.output_dir, os.path.basename(self.xml_path).split('.')[0] + ".epub")
            
            with open(html_path, 'r', encoding='utf-8') as html_file:
                with open(epub_path, 'w', encoding='utf-8') as epub_file:
                    # Add EPUB-specific content (simplified for demo)
                    epub_file.write("EPUB VERSION\n\n")
                    epub_file.write(html_file.read())
            
            return epub_path
            
        except Exception as e:
            logger.error(f"Error converting to EPUB: {str(e)}")
            return None
    
    def _convert_to_mobi(self) -> Optional[str]:
        """
        Convert XML to MOBI
        Returns path to MOBI file or None if conversion failed
        
        Note: In a real implementation, this would use a tool like Calibre's
        ebook-convert command line tool to create a proper MOBI file.
        This is a simplified example.
        """
        try:
            # In a real implementation, this would convert XML or EPUB to MOBI
            # using a tool like Calibre's ebook-convert
            # For this demo, we'll create a simple MOBI-like file
            
            # Start with HTML conversion
            html_path = self._convert_to_html()
            if not html_path:
                return None
            
            # Create a simple MOBI-like file (not a real MOBI)
            mobi_path = os.path.join(self.output_dir, os.path.basename(self.xml_path).split('.')[0] + ".mobi")
            
            with open(html_path, 'r', encoding='utf-8') as html_file:
                with open(mobi_path, 'w', encoding='utf-8') as mobi_file:
                    # Add MOBI-specific content (simplified for demo)
                    mobi_file.write("MOBI VERSION\n\n")
                    mobi_file.write(html_file.read())
            
            return mobi_path
            
        except Exception as e:
            logger.error(f"Error converting to MOBI: {str(e)}")
            return None