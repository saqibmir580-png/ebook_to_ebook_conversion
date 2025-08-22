import os
import json
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
import logging
from xml.etree import ElementTree as ET

# Try multiple import patterns for rapid_latex_ocr
LatexOCR = None
try:
    # The correct import for rapid-latex-ocr 0.0.9
    from rapid_latex_ocr.main import LaTeXOCR as LatexOCR
    print("✅ Successfully imported LaTeXOCR from rapid_latex_ocr.main")
except ImportError:
    try:
        from rapid_latex_ocr import LaTeXOCR as LatexOCR
        print("✅ Successfully imported LaTeXOCR from rapid_latex_ocr")
    except ImportError:
        try:
            # Fallback to older patterns
            from rapid_latex_ocr.rapid_latex_ocr import RapidLatexOCR as LatexOCR
            print("✅ Successfully imported RapidLatexOCR from rapid_latex_ocr.rapid_latex_ocr")
        except ImportError:
            try:
                from rapid_latex_ocr import RapidLatexOCR as LatexOCR
                print("✅ Successfully imported RapidLatexOCR from rapid_latex_ocr")
            except ImportError:
                print("Warning: Could not import LaTeX OCR. LaTeX OCR functionality will be disabled.")
                print("Please install with: pip install rapid-latex-ocr==0.0.9")
                LatexOCR = None

from app.core.config import settings
from app.utils.formula_converter import FormulaConverter
from app.services.conversion import EbookConverter

# Define paths to the downloaded model files
# NOTE: You must download these models and place them in a 'backend/models' directory.
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'models')
IMAGE_RESIZER_PATH = os.path.join(MODELS_DIR, 'image_resizer.onnx')
ENCODER_PATH = os.path.join(MODELS_DIR, 'encoder.onnx')
DECODER_PATH = os.path.join(MODELS_DIR, 'decoder.onnx')
TOKENIZER_PATH = os.path.join(MODELS_DIR, 'tokenizer.json')

# Define the project root to construct absolute paths for file operations
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ABS_EXTRACTED_IMAGES_DIR = os.path.join(PROJECT_ROOT, settings.EXTRACTED_IMAGES_DIR)

logger = logging.getLogger(__name__)

# Initialize LaTeX OCR model
try:
    if LatexOCR and all(os.path.exists(p) for p in [IMAGE_RESIZER_PATH, ENCODER_PATH, DECODER_PATH, TOKENIZER_PATH]):
        latex_ocr_model = LatexOCR(
            image_resizer_path=IMAGE_RESIZER_PATH,
            encoder_path=ENCODER_PATH,
            decoder_path=DECODER_PATH,
            tokenizer_json=TOKENIZER_PATH
        )
    else:
        if not LatexOCR:
            print("Warning: LaTeX OCR class not available due to import issues.")
        else:
            print("Warning: LaTeX OCR model files not found. Please download them and place them in the 'backend/models' directory.")
        latex_ocr_model = None
except Exception as e:
    print(f"Warning: Could not initialize LaTeX OCR model: {e}")
    latex_ocr_model = None

# Configure Tesseract path for Windows
# This might need to be configured in settings
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS

def extract_images_from_pdf(pdf_path: str, output_folder: str) -> list[str]:
    images = []
    try:
        os.makedirs(output_folder, exist_ok=True)
        pdf_document = fitz.open(pdf_path)
        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        img_count = 0
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            image_list = page.get_images(full=True)
            if image_list:
                for img_index, img in enumerate(image_list, 1):
                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        img_count += 1
                        img_filename = f"{base_filename}_img_{img_count}.jpeg"
                        img_path = os.path.join(output_folder, img_filename)
                        logging.info(f"Saving extracted image to: {img_path}")
                        with open(img_path, "wb") as img_file:
                            img_file.write(image_bytes)
                        rel_path = f"extracted_images/{img_filename}"
                        images.append(rel_path)
                    except Exception as img_err:
                        print(f"Error extracting image {img_index} from page {page_num + 1}: {img_err}")
        pdf_document.close()
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
    return images

def clean_latex_formula(formula: str) -> str:
    if not formula:
        return formula
    formula = formula.replace('\n', ' ')
    formula = re.sub(r'\s+', ' ', formula)
    formula = formula.strip()
    formula = formula.replace(' ,', ',')
    formula = formula.replace(' .', '.')
    formula = formula.replace(' = ', '=')
    formula = formula.replace(' =', '=')
    formula = formula.replace('= ', '=')
    formula = re.sub(r'\\left\s+', r'\\left', formula)
    formula = re.sub(r'\\right\s+', r'\\right', formula)
    formula = re.sub(r'\s+\\left', r'\\left', formula)
    formula = re.sub(r'\s+\\right', r'\\right', formula)
    formula = re.sub(r'\s*([+\-*/=])\s*', r'\1', formula)
    return formula

def is_likely_formula_image(image, min_width=50, min_height=20, max_width=800, max_height=200):
    """
    Heuristic to determine if an image is likely to contain a formula
    """
    width, height = image.size
    
    # Size-based filtering
    if width < min_width or height < min_height:
        return False
    if width > max_width or height > max_height:
        return False
    
    # Aspect ratio check - formulas are typically wider than tall
    aspect_ratio = width / height
    if aspect_ratio < 1.5 or aspect_ratio > 10:
        return False
    
    # Convert to grayscale for analysis
    gray = image.convert('L')
    pixels = list(gray.getdata())
    
    # Check if image has enough contrast (not just solid color)
    min_pixel = min(pixels)
    max_pixel = max(pixels)
    if max_pixel - min_pixel < 50:  # Low contrast
        return False
    
    # Check for white background (common in formula images)
    white_pixels = sum(1 for p in pixels if p > 240)
    white_ratio = white_pixels / len(pixels)
    if white_ratio < 0.3:  # Less than 30% white pixels
        return False
    
    return True

def extract_formula_from_image(image_path: str) -> str:
    """Extract LaTeX formula from image with pre-filtering and convert to readable format"""
    try:
        # Load and check if image is likely a formula
        image = Image.open(image_path)
        
        if not is_likely_formula_image(image):
            return ""
        
        # Only run expensive LaTeX OCR on likely formula images
        if latex_ocr_model:
            result = latex_ocr_model(image_path)
            
            # Handle different return formats
            if isinstance(result, tuple):
                latex_text = result[0] if result else ""
            else:
                latex_text = result if result else ""
            
            # Basic validation of LaTeX output
            if latex_text and len(latex_text.strip()) > 3:
                # Check if result contains mathematical symbols
                math_indicators = ['\\', '{', '}', '^', '_', '\\frac', '\\sum', '\\int', '=', '+', '-', '*']
                if any(indicator in latex_text for indicator in math_indicators):
                    # Clean the LaTeX formula
                    cleaned_latex = clean_latex_formula(latex_text.strip())
                    print(f"DEBUG: Extracted LaTeX formula: {cleaned_latex}")
                    
                    # Convert to human-readable format using formula converter
                    if formula_converter:
                        try:
                            readable_formula = formula_converter.convert_to_readable(cleaned_latex)
                            print(f"DEBUG: Converted to readable: {readable_formula}")
                            return readable_formula
                        except Exception as conv_error:
                            print(f"DEBUG: Formula conversion failed: {conv_error}")
                            # Fallback to cleaned LaTeX if conversion fails
                            return cleaned_latex
                    else:
                        print("DEBUG: Formula converter not available, returning cleaned LaTeX")
                        return cleaned_latex
        
        return ""
        
    except Exception as e:
        print(f"DEBUG: Formula extraction failed for {image_path}: {e}")
        return ""

def process_file(file_path: str) -> tuple[str, list[dict], list[str], str]:
    text_output = ''
    extracted_images = []
    json_data = []
    image_counter = 0
    html_path = None # Initialize html_path
    
    print(f"DEBUG: Starting to process file: {file_path}")
    
    try:
        if file_path.lower().endswith('.pdf'):
            doc = fitz.open(file_path)
            print(f"DEBUG: Opened PDF with {len(doc)} pages")
            
            # Enhanced extraction with layout preservation
            all_text = []
            pages_json = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text with layout information
                page_dict = page.get_text("dict", sort=True)
                page_width = page.rect.width
                page_height = page.rect.height
                
                # Process blocks to maintain structure with enhanced formatting
                page_blocks = []
                page_text_parts = []
                
                for block in page_dict["blocks"]:
                    if block["type"] == 0:  # text block
                        block_text = ""
                        block_html = ""
                        block_spans = []
                        
                        for line in block["lines"]:
                            line_text = ""
                            line_html = ""
                            line_spans = []
                            
                            for span in line["spans"]:
                                span_text = span.get("text", "")
                                if span_text.strip():
                                    # Extract font information
                                    font_name = span.get("font", "")
                                    font_size = span.get("size", 12)
                                    font_flags = span.get("flags", 0)
                                    color = span.get("color", 0)
                                    
                                    # Determine font style
                                    is_bold = bool(font_flags & 2**4) or "bold" in font_name.lower()
                                    is_italic = bool(font_flags & 2**1) or "italic" in font_name.lower()
                                    is_superscript = font_size < 10 and span.get("bbox", [0,0,0,0])[1] < line.get("bbox", [0,0,0,0])[1]
                                    
                                    # Convert color to hex
                                    if color != 0:
                                        hex_color = f"#{color:06x}"
                                    else:
                                        hex_color = "#000000"
                                    
                                    # Build styled HTML
                                    styled_text = span_text
                                    if is_bold:
                                        styled_text = f"<strong>{styled_text}</strong>"
                                    if is_italic:
                                        styled_text = f"<em>{styled_text}</em>"
                                    if is_superscript:
                                        styled_text = f"<sup>{styled_text}</sup>"
                                    
                                    # Add font size and color styling
                                    if font_size != 12 or hex_color != "#000000":
                                        styled_text = f'<span style="font-size: {font_size}px; color: {hex_color};">{styled_text}</span>'
                                    
                                    line_text += span_text
                                    line_html += styled_text
                                    
                                    # Store span information
                                    line_spans.append({
                                        "text": span_text,
                                        "font": font_name,
                                        "size": font_size,
                                        "bold": is_bold,
                                        "italic": is_italic,
                                        "superscript": is_superscript,
                                        "color": hex_color,
                                        "bbox": span.get("bbox", [0, 0, 0, 0])
                                    })
                            
                            if line_text.strip():
                                block_text += line_text + "\n"
                                block_html += line_html + "<br>"
                                block_spans.extend(line_spans)
                        
                        if block_text.strip():
                            page_text_parts.append(block_text.strip())
                            
                            # Determine block type based on content and formatting
                            block_type = "text"
                            if any(span["size"] > 16 for span in block_spans):
                                block_type = "title"
                            elif any(span["size"] > 14 for span in block_spans):
                                block_type = "heading"
                            elif "ABSTRACT" in block_text.upper():
                                block_type = "abstract"
                            elif block_text.strip().startswith("Keywords:"):
                                block_type = "keywords"
                            elif any("@" in span["text"] for span in block_spans):
                                block_type = "author"
                            
                            page_blocks.append({
                                "type": block_type,
                                "content": block_text.strip(),
                                "html_content": block_html.strip(),
                                "spans": block_spans,
                                "x": block.get("bbox", [0, 0, 0, 0])[0],
                                "y": block.get("bbox", [0, 0, 0, 0])[1],
                                "width": block.get("bbox", [0, 0, 0, 0])[2] - block.get("bbox", [0, 0, 0, 0])[0],
                                "height": block.get("bbox", [0, 0, 0, 0])[3] - block.get("bbox", [0, 0, 0, 0])[1]
                            })
                    
                    elif block["type"] == 1:  # image block
                        try:
                            image_bytes = block.get("image")
                            bbox = block.get("bbox", [0, 0, 0, 0])
                            
                            if image_bytes:
                                image_counter += 1
                                img_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_img_{image_counter}.png"
                                img_path = os.path.join(settings.EXTRACTED_IMAGES_DIR, img_filename)
                                os.makedirs(settings.EXTRACTED_IMAGES_DIR, exist_ok=True)
                                logging.info(f"Saving extracted image to: {img_path}")
                                with open(img_path, "wb") as img_file:
                                    img_file.write(image_bytes)
                                
                                rel_path = os.path.join(settings.EXTRACTED_IMAGES_DIR, img_filename).replace("\\", "/")
                                extracted_images.append(rel_path)
                                print(f"DEBUG: Added image to extracted_images: {rel_path}")
                                
                                # Extract formula from image
                                formula = extract_formula_from_image(img_path)
                                if formula:
                                    page_blocks.append({
                                        "type": "formula",
                                        "content": formula,
                                        "x": bbox[0],
                                        "y": bbox[1],
                                        "width": bbox[2] - bbox[0],
                                        "height": bbox[3] - bbox[1]
                                    })
                                    print(f"DEBUG: Added formula block for image: {img_filename}")
                                else:
                                    page_blocks.append({
                                        "type": "image",
                                        "path": rel_path,
                                        "x": bbox[0],
                                        "y": bbox[1],
                                        "width": bbox[2] - bbox[0],
                                        "height": bbox[3] - bbox[1]
                                    })
                                    print(f"DEBUG: Added image block for: {img_filename}")
                                
                                print(f"DEBUG: Extracted image {img_filename} at position ({bbox[0]}, {bbox[1]})")
                        
                        except Exception as img_error:
                            print(f"DEBUG: Failed to extract image: {img_error}")
                
                # Combine text for this page
                if page_text_parts:
                    page_text = "\n\n".join(page_text_parts)
                    all_text.append(f"=== Page {page_num + 1} ===\n{page_text}")
                
                pages_json.append({
                    "page_num": page_num + 1,
                    "width": page_width,
                    "height": page_height,
                    "blocks": page_blocks
                })
                
                print(f"DEBUG: Page {page_num + 1} extracted {len(''.join(page_text_parts))} characters, {len([b for b in page_blocks if b['type'] == 'image'])} images")
            
            text_output = "\n\n".join(all_text)
            json_data = pages_json
            doc.close()
            
            print(f"DEBUG: Final extraction - Total characters: {len(text_output)}, Images: {len(extracted_images)}")
            print(f"DEBUG: Text preview: {text_output[:200] if text_output else 'EMPTY'}")
            print(f"DEBUG: Extracted images list: {extracted_images}")
            
            # --- Direct HTML Generation with Base64 Images ---
            try:
                project_name = os.path.splitext(os.path.basename(file_path))[0]
                print(f"DEBUG: Generating HTML for {project_name}")
                print(f"DEBUG: About to process {len(extracted_images)} images for HTML embedding")
                
                # Generate HTML directly with embedded images
                html_content = []
                html_content.append("<!DOCTYPE html>")
                html_content.append("<html lang='en'>")
                html_content.append("<head>")
                html_content.append("  <meta charset='UTF-8'>")
                html_content.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
                html_content.append(f"  <title>{project_name}</title>")
                html_content.append("  <style>")
                html_content.append("    body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }")
                html_content.append("    h1 { text-align: center; }")
                html_content.append("    .page { border-bottom: 1px solid #ccc; padding-bottom: 10px; margin-bottom: 20px; }")
                html_content.append("    .page-images { margin: 20px 0; }")
                html_content.append("    .page-images img { max-width: 100%; margin: 10px 0; border: 1px solid #ddd; }")
                html_content.append("  </style>")
                html_content.append("</head>")
                html_content.append("<body>")
                html_content.append(f"  <h1>{project_name}</h1>")
                
                # Add content from each page
                for page_data in json_data:
                    page_num = page_data.get('page_num', 1)
                    html_content.append(f"  <div class='page'>")
                    html_content.append(f"    <h3>Page {page_num}</h3>")
                    
                    # Get all blocks for this page and sort by Y position (top to bottom)
                    page_blocks = page_data.get('blocks', [])
                    
                    # Filter and sort all blocks by Y coordinate to maintain proper reading order
                    all_blocks = []
                    for block in page_blocks:
                        if block.get('type') == 'text' and block.get('content', '').strip():
                            all_blocks.append({
                                'type': 'text',
                                'content': block['content'],
                                'y': block.get('y', 0),
                                'x': block.get('x', 0)
                            })
                        elif block.get('type') == 'image' and block.get('path'):
                            all_blocks.append({
                                'type': 'image',
                                'path': block['path'],
                                'y': block.get('y', 0),
                                'x': block.get('x', 0),
                                'width': block.get('width', 0),
                                'height': block.get('height', 0)
                            })
                    
                    # Sort blocks by Y coordinate (top to bottom), then by X coordinate (left to right)
                    all_blocks.sort(key=lambda b: (b['y'], b['x']))
                    
                    # Process blocks in proper order
                    for block in all_blocks:
                        if block['type'] == 'text':
                            content = block['content'].replace('\n', '<br>')
                            html_content.append(f"    <p>{content}</p>")
                        
                        elif block['type'] == 'image':
                            img_path = block['path']
                            try:
                                print(f"DEBUG: Processing page {page_num} image at position ({block['x']}, {block['y']}): {img_path}")
                                
                                # Get just the filename for better path resolution
                                img_filename = os.path.basename(img_path)
                                
                                # Try multiple path construction strategies
                                potential_paths = [
                                    # Path 1: Direct path if absolute
                                    img_path if os.path.isabs(img_path) else None,
                                    
                                    # Path 2: PROJECT_ROOT + static + img_path (if img_path includes extracted_images)
                                    os.path.join(PROJECT_ROOT, 'static', img_path) if 'extracted_images' in img_path else None,
                                    
                                    # Path 3: PROJECT_ROOT + static + extracted_images + filename
                                    os.path.join(PROJECT_ROOT, 'static', 'extracted_images', img_filename),
                                    
                                    # Path 4: Current working directory + static + extracted_images + filename
                                    os.path.join(os.getcwd(), 'static', 'extracted_images', img_filename),
                                    
                                    # Path 5: Settings STATIC_DIR + extracted_images + filename
                                    os.path.join(settings.STATIC_DIR, 'extracted_images', img_filename) if hasattr(settings, 'STATIC_DIR') else None,
                                    
                                    # Path 6: Legacy path - PROJECT_ROOT + extracted_images + filename
                                    os.path.join(PROJECT_ROOT, 'extracted_images', img_filename),
                                ]
                                
                                # Filter out None values and duplicates
                                potential_paths = list(dict.fromkeys([p for p in potential_paths if p is not None]))
                                
                                abs_image_path = None
                                for j, path in enumerate(potential_paths):
                                    print(f"DEBUG: Trying path {j+1}: {path}")
                                    if os.path.exists(path) and os.path.isfile(path):
                                        abs_image_path = path
                                        print(f"DEBUG: Found image at path {j+1}: {abs_image_path}")
                                        break
                                
                                if abs_image_path:
                                    # Read and encode image as Base64
                                    with open(abs_image_path, "rb") as image_file:
                                        import base64
                                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                                        
                                        # Determine image format
                                        ext = os.path.splitext(abs_image_path)[1].lower().lstrip('.')
                                        if ext == 'jpg':
                                            ext = 'jpeg'
                                        elif ext not in ['png', 'jpeg', 'gif', 'webp', 'svg']:
                                            ext = 'png'  # Default fallback
                                        
                                        data_uri = f"data:image/{ext};base64,{encoded_string}"
                                        
                                        # Add image with position information
                                        html_content.append(f'''    <div class="image-block" style="margin: 15px 0; text-align: center; position: relative;">
      <img src="{data_uri}" alt="Image at position ({block['x']}, {block['y']})" 
           style="max-width: 100%; max-height: 600px; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
      <p style="font-size: 10px; color: #666; margin-top: 5px;">
        {img_filename} | Position: ({block['x']:.0f}, {block['y']:.0f}) | Size: {block['width']:.0f}×{block['height']:.0f}
      </p>
    </div>''')
                                        print(f"DEBUG: Successfully embedded image at position ({block['x']}, {block['y']}): {img_filename}")
                                else:
                                    print(f"DEBUG: Image not found at position ({block['x']}, {block['y']}): {img_filename}")
                                    html_content.append(f'''    <div class="image-error" style="margin: 15px 0; padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">
      <p style="color: #856404; margin: 0;">Image not found: {img_filename}</p>
      <p style="font-size: 10px; color: #856404; margin: 5px 0 0 0;">Position: ({block['x']:.0f}, {block['y']:.0f}) | Original path: {img_path}</p>
    </div>''')
                                    
                            except Exception as img_error:
                                print(f"DEBUG: Failed to embed image at position ({block['x']}, {block['y']}): {img_path}: {img_error}")
                                html_content.append(f'''    <div class="image-error" style="margin: 15px 0; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;">
      <p style="color: #721c24; margin: 0;">Error loading image: {os.path.basename(img_path)}</p>
      <p style="font-size: 10px; color: #721c24; margin: 5px 0 0 0;">Position: ({block['x']:.0f}, {block['y']:.0f}) | Error: {str(img_error)}</p>
    </div>''')
                    
                    html_content.append("  </div>")
                
                html_content.append("</body>")
                html_content.append("</html>")
                
                # Save the HTML file
                html_filename = f"{project_name}.html"
                html_path = os.path.join(settings.OUTPUT_DIR, html_filename)
                os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(html_content))
                print(f"DEBUG: Saved HTML file to {html_path}")

            except Exception as conversion_error:
                print(f"ERROR: Failed during HTML conversion step: {conversion_error}")
                html_path = None # Ensure path is None if conversion fails

        else:
            # Handle image files
            image = Image.open(file_path)
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            text_output = pytesseract.image_to_string(image)
            
            # Save the image for display
            img_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.png"
            img_path = os.path.join(settings.EXTRACTED_IMAGES_DIR, img_filename)
            os.makedirs(settings.EXTRACTED_IMAGES_DIR, exist_ok=True)
            image.save(img_path, 'PNG')
            logging.info(f"Saving single image to: {img_path}")
            rel_path = os.path.join(settings.EXTRACTED_IMAGES_DIR, img_filename).replace("\\", "/")
            extracted_images = [rel_path]
            
            json_data = [{
                "page_num": 1,
                "width": image.width,
                "height": image.height,
                "blocks": [
                    {
                        "type": "text",
                        "content": text_output,
                        "x": 0,
                        "y": 0,
                        "width": image.width,
                        "height": image.height
                    } if text_output.strip() else {},
                    {
                        "type": "image",
                        "path": rel_path,
                        "x": 0,
                        "y": 0,
                        "width": image.width,
                        "height": image.height
                    }
                ]
            }]
            
    except Exception as e:
        print(f"ERROR: Failed to process file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        
    return text_output, json_data, extracted_images, html_path
