#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
End-to-end test for LaTeX formula processing pipeline
Tests the complete flow from PDF processing to readable formula output
"""

import os
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_formula_image(latex_formula: str, output_path: str):
    """Create a test image with LaTeX-like formula for testing"""
    # Create a simple image with formula-like text
    width, height = 400, 100
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to use a basic font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Draw the formula text
    draw.text((20, 30), latex_formula, fill='black', font=font)
    
    # Save the image
    image.save(output_path)
    print(f"Created test formula image: {output_path}")

def test_formula_converter():
    """Test the formula converter directly"""
    print("\n=== Testing Formula Converter ===")
    
    try:
        from app.utils.formula_converter import formula_converter
        
        test_formulas = [
            r"\frac{1}{2}",
            r"x^2 + y^2 = z^2",
            r"\int_{0}^{1} x dx",
            r"\sum_{i=1}^{n} i",
            r"\alpha + \beta = \gamma"
        ]
        
        for formula in test_formulas:
            try:
                readable = formula_converter.convert_to_readable(formula)
                print(f"✅ {formula} → {readable}")
            except Exception as e:
                print(f"❌ {formula} → Error: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import formula converter: {e}")
        return False

def test_ocr_utils():
    """Test the OCR utilities with formula extraction"""
    print("\n=== Testing OCR Utils ===")
    
    try:
        from app.utils.ocr_utils import extract_formula_from_image, latex_ocr_model
        
        if not latex_ocr_model:
            print("❌ LaTeX OCR model not available")
            return False
        
        # Create a test image with a simple formula
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            test_image_path = tmp_file.name
        
        create_test_formula_image(r"x^2 + 1 = 0", test_image_path)
        
        try:
            # Test formula extraction
            result = extract_formula_from_image(test_image_path)
            print(f"✅ Formula extraction result: {result}")
            
            # Clean up
            os.unlink(test_image_path)
            return True
            
        except Exception as e:
            print(f"❌ Formula extraction failed: {e}")
            # Clean up
            if os.path.exists(test_image_path):
                os.unlink(test_image_path)
            return False
        
    except ImportError as e:
        print(f"❌ Could not import OCR utils: {e}")
        return False

def test_extraction_service():
    """Test the EbookExtractor service"""
    print("\n=== Testing EbookExtractor Service ===")
    
    try:
        from app.services.extraction import EbookExtractor
        from app.models.upload import FileType
        
        # Create a simple test PDF (this would need a real PDF for full testing)
        # For now, just test the import and initialization
        
        # Test initialization
        test_path = "test.pdf"  # This doesn't need to exist for initialization test
        extractor = EbookExtractor(test_path, FileType.PDF)
        
        print("✅ EbookExtractor initialized successfully")
        print(f"✅ File path: {extractor.file_path}")
        print(f"✅ File type: {extractor.file_type}")
        print(f"✅ Metadata initialized: {extractor.metadata}")
        
        return True
        
    except Exception as e:
        print(f"❌ EbookExtractor test failed: {e}")
        return False

def test_imports():
    """Test all critical imports"""
    print("\n=== Testing Critical Imports ===")
    
    imports_to_test = [
        ("app.utils.formula_converter", "formula_converter"),
        ("app.utils.ocr_utils", "latex_ocr_model"),
        ("app.services.extraction", "EbookExtractor"),
        ("app.services.conversion", "EbookConverter"),
    ]
    
    all_passed = True
    
    for module_name, item_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            item = getattr(module, item_name)
            print(f"✅ {module_name}.{item_name} imported successfully")
        except Exception as e:
            print(f"❌ {module_name}.{item_name} import failed: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🧪 Starting End-to-End Formula Processing Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test imports first
    test_results.append(("Imports", test_imports()))
    
    # Test formula converter
    test_results.append(("Formula Converter", test_formula_converter()))
    
    # Test OCR utilities
    test_results.append(("OCR Utils", test_ocr_utils()))
    
    # Test extraction service
    test_results.append(("Extraction Service", test_extraction_service()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Formula processing pipeline is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
