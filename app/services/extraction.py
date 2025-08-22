import os
import time
from typing import Dict, Any, List, Tuple
import PyPDF2
from docx import Document
import ebooklib
from ebooklib import epub
from PIL import Image
import pytesseract
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
from app.models.upload import FileType
from app.utils.ocr_utils import process_file

logger = logging.getLogger(__name__)


class EbookExtractor:
    def __init__(self, file_path: str, file_type: FileType):
        self.file_path = file_path
        self.file_type = file_type
        self.metadata = {
            "page_count": 0,
            "image_count": 0,
            "formula_count": 0,
            "processing_time": 0,
        }
        self.xml_path = None
        
    def extract(self) -> str:
        """
        Extract content from e-book and save to XML
        Returns the path to the XML file
        """
        start_time = time.time()
        
        try:
            if self.file_type == FileType.PDF:
                text, images, formulas, structure = self._extract_from_pdf()
            elif self.file_type == FileType.DOCX:
                text, images, formulas, structure = self._extract_from_docx()
            elif self.file_type == FileType.EPUB:
                text, images, formulas, structure = self._extract_from_epub()
            else:
                raise ValueError(f"Unsupported file type: {self.file_type}")
                
            # Save to XML
            xml_path = self._create_xml(text, images, formulas, structure)
            
            # Record processing time
            self.metadata["processing_time"] = time.time() - start_time
            
            return xml_path
            
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            raise
    
    def _extract_from_pdf(self) -> Tuple[List[Dict], List[Dict], List[str], Dict]:
        """Extract content from PDF file using proper LaTeX OCR"""
        try:
            # Use the proper OCR processing pipeline
            text_output, json_data, extracted_images = process_file(self.file_path)
            
            # Parse the JSON data to extract formulas
            formulas = []
            structure = {"fonts": [], "layout": []}
            
            # Process the JSON data from OCR to extract formulas
            for page_data in json_data:
                for block in page_data.get("blocks", []):
                    if block.get("type") == "formula":
                        formula_content = block.get("content", "")
                        if formula_content:
                            formulas.append(f"Formula on page {page_data.get('page_num', 1)}: {formula_content}")
            
            # Update metadata
            self.metadata["page_count"] = len(json_data) if json_data else 1
            self.metadata["image_count"] = len(extracted_images)
            self.metadata["formula_count"] = len(formulas)
            
            print(f"DEBUG: Extracted {len(formulas)} formulas using LaTeX OCR")
            for i, formula in enumerate(formulas[:3]):  # Show first 3 formulas for debugging
                print(f"DEBUG: Formula {i+1}: {formula}")
            
            # Return the structured JSON data instead of flattened text
            return json_data, extracted_images, formulas, structure
            
        except Exception as e:
            logger.error(f"Error extracting PDF content with LaTeX OCR: {str(e)}")
            # Fallback to basic extraction
            return self._extract_from_pdf_basic()
    
    def _extract_from_pdf_basic(self) -> Tuple[List[str], List[str], List[str], Dict]:
        """Fallback basic PDF extraction without LaTeX OCR"""
        text_by_page = []
        images = []
        formulas = []
        structure = {"fonts": [], "layout": []}
        
        try:
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    text_by_page.append(text)
                    
                    # Simple formula detection (looking for math symbols)
                    math_symbols = re.findall(r'[=+\-*/^√∫∑∏πΔ∇]+', text)
                    if math_symbols:
                        formulas.extend([f"Formula on page {page_num + 1}: {m}" for m in math_symbols])
                
                # Update metadata
                self.metadata["page_count"] = len(pdf_reader.pages)
                self.metadata["image_count"] = 0  # Basic extraction doesn't handle images
                self.metadata["formula_count"] = len(formulas)
                
                # In a real implementation, more detailed PDF structure extraction would happen here
                
            return text_by_page, images, formulas, structure
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}")
            raise
    
    def _extract_from_docx(self) -> Tuple[List[str], List[Dict], List[str], Dict]:
        """Extract content from DOCX file"""
        text_by_paragraph = []
        images = []
        formulas = []
        structure = {"fonts": [], "layout": []}
        
        try:
            doc = Document(self.file_path)
            
            # Extract text
            for para in doc.paragraphs:
                text_by_paragraph.append(para.text)
                
                # Simple formula detection
                math_symbols = re.findall(r'[=+\-*/^]+', para.text)
                if math_symbols:
                    formulas.extend([f"Formula: {m}" for m in math_symbols])
                
            # Extract fonts and styles
            for style in doc.styles:
                if hasattr(style, 'font') and style.font:
                    if style.font.name:
                        structure["fonts"].append(style.font.name)
            
            # Update metadata
            self.metadata["page_count"] = len(text_by_paragraph) // 40 + 1  # Rough estimate
            
            return text_by_paragraph, images, formulas, structure
            
        except Exception as e:
            logger.error(f"Error extracting DOCX content: {str(e)}")
            raise
    
    def _extract_from_epub(self) -> Tuple[List[str], List[Dict], List[str], Dict]:
        """Extract content from EPUB file"""
        text_by_chapter = []
        images = []
        formulas = []
        structure = {"fonts": [], "layout": []}
        
        try:
            book = epub.read_epub(self.file_path)
            
            # Extract text
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content().decode('utf-8')
                    # Simple HTML parsing - in a real implementation, use a proper HTML parser
                    text_only = re.sub(r'<[^>]+>', ' ', content)
                    text_by_chapter.append(text_only)
                    
                    # Simple formula detection
                    math_symbols = re.findall(r'[=+\-*/^]+', text_only)
                    if math_symbols:
                        formulas.extend([f"Formula: {m}" for m in math_symbols])
                
                # Count images
                elif item.get_type() == ebooklib.ITEM_IMAGE:
                    images.append({
                        "name": item.get_name(),
                        "path": f"/images/image.jpg"  # Would save in a real implementation
                    })
            
            # Update metadata
            self.metadata["page_count"] = len(text_by_chapter)
            self.metadata["image_count"] = len(images)
            
            return text_by_chapter, images, formulas, structure
            
        except Exception as e:
            logger.error(f"Error extracting EPUB content: {str(e)}")
            raise
    
    def _create_xml(self, text, images, formulas, structure) -> str:
        """Create XML from extracted content"""
        try:
            # Create XML root
            root = ET.Element("ebook")
            
            # Add metadata
            metadata = ET.SubElement(root, "metadata")
            ET.SubElement(metadata, "file_type").text = self.file_type.value
            ET.SubElement(metadata, "page_count").text = str(self.metadata["page_count"])
            ET.SubElement(metadata, "image_count").text = str(len(images))
            ET.SubElement(metadata, "formula_count").text = str(len(formulas))
            
            # Add date/time using <ddt> tags as required
            ddt = ET.SubElement(metadata, "ddt")
            ddt.text = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Add content
            content = ET.SubElement(root, "content")
            
            # Add text from structured data
            text_section = ET.SubElement(content, "text")
            for i, page_data in enumerate(text):  # `text` is now `json_data`
                page_elem = ET.SubElement(text_section, "page")
                page_elem.set("id", str(i + 1))
                
                # Add blocks with their semantic types
                for block in page_data.get("blocks", []):
                    block_type = block.get("type")
                    # Skip formula and image blocks as they are handled separately
                    if block_type in ["formula", "image"]:
                        continue
                    
                    # Use block type as the tag name, default to 'text'
                    tag_name = block_type or "text"
                    block_elem = ET.SubElement(page_elem, tag_name)
                    block_elem.text = block.get("content", "")
            
            # Add images
            if images:
                logger.info(f"Adding {len(images)} images to XML")
                images_section = ET.SubElement(content, "images")
                for i, img_path in enumerate(images):
                    logger.info(f"Adding image {i+1}: {img_path}")
                    # Use TEI namespace structure that the HTML converter expects
                    graphic = ET.SubElement(images_section, "{http://www.tei-c.org/ns/1.0}graphic")
                    # img_path already includes 'extracted_images/' prefix from ocr_utils.py
                    full_url = f"http://localhost:8000/static/{img_path}"
                    graphic.set("{http://www.w3.org/1999/xlink}href", full_url)
                    graphic.set("id", str(i + 1))
                    logger.info(f"Image URL set to: {full_url}")
            else:
                logger.warning("No images to add to XML")
            
            # Add formulas
            if formulas:
                formulas_section = ET.SubElement(content, "formulas")
                for i, formula in enumerate(formulas):
                    formula_elem = ET.SubElement(formulas_section, "formula")
                    formula_elem.set("id", str(i + 1))
                    formula_elem.text = formula
            
            # Add structure information
            structure_section = ET.SubElement(content, "structure")
            
            # Add fonts
            if structure["fonts"]:
                fonts_section = ET.SubElement(structure_section, "fonts")
                for i, font in enumerate(structure["fonts"]):
                    font_elem = ET.SubElement(fonts_section, "font")
                    font_elem.set("id", str(i + 1))
                    font_elem.text = font
            
            # Add layout
            if structure["layout"]:
                layout_section = ET.SubElement(structure_section, "layout")
                for i, layout in enumerate(structure["layout"]):
                    layout_elem = ET.SubElement(layout_section, "element")
                    layout_elem.set("id", str(i + 1))
                    layout_elem.text = str(layout)
            
            # Add entities using <ent> tags as required
            entities_section = ET.SubElement(content, "entities")
            ent = ET.SubElement(entities_section, "ent")
            ent.set("type", "document")
            ent.text = os.path.basename(self.file_path)
            
            # Convert to pretty XML string
            xml_str = minidom.parseString(ET.tostring(root, 'utf-8')).toprettyxml(indent="  ")
            
            # Save XML to file
            output_dir = os.path.dirname(self.file_path)
            xml_filename = os.path.basename(self.file_path).split('.')[0] + ".xml"
            xml_path = os.path.join(output_dir, xml_filename)
            
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            
            self.xml_path = xml_path
            return xml_path
            
        except Exception as e:
            logger.error(f"Error creating XML: {str(e)}")
            raise