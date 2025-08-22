#!/usr/bin/env python
"""
Test the fixed import for rapid_latex_ocr
"""

# Try the same import pattern as in ocr_utils.py
LatexOCR = None
try:
    # Try the most common import pattern first
    from rapid_latex_ocr.rapid_latex_ocr import RapidLatexOCR as LatexOCR
    print("✅ Successfully imported RapidLatexOCR from rapid_latex_ocr.rapid_latex_ocr")
except ImportError:
    try:
        from rapid_latex_ocr import RapidLatexOCR as LatexOCR
        print("✅ Successfully imported RapidLatexOCR from rapid_latex_ocr")
    except ImportError:
        try:
            from rapid_latex_ocr.main import RapidLatexOCR as LatexOCR
            print("✅ Successfully imported RapidLatexOCR from rapid_latex_ocr.main")
        except ImportError:
            try:
                # Check if there's a different class name
                import rapid_latex_ocr
                if hasattr(rapid_latex_ocr, 'rapid_latex_ocr'):
                    LatexOCR = rapid_latex_ocr.rapid_latex_ocr
                    print("✅ Successfully imported via rapid_latex_ocr.rapid_latex_ocr")
                elif hasattr(rapid_latex_ocr, 'RapidLatexOCR'):
                    LatexOCR = rapid_latex_ocr.RapidLatexOCR
                    print("✅ Successfully imported RapidLatexOCR via module attribute")
                else:
                    raise ImportError("No suitable class found")
            except (ImportError, AttributeError):
                print("❌ Could not import RapidLatexOCR")
                LatexOCR = None

if LatexOCR:
    print(f"✅ Import successful! Class: {LatexOCR}")
    
    # Test initialization with model files
    import os
    models_dir = "models"
    if os.path.exists(models_dir):
        model_files = ["image_resizer.onnx", "encoder.onnx", "decoder.onnx", "tokenizer.json"]
        if all(os.path.exists(os.path.join(models_dir, f)) for f in model_files):
            try:
                latex_ocr = LatexOCR(
                    image_resizer_path=os.path.join(models_dir, "image_resizer.onnx"),
                    encoder_path=os.path.join(models_dir, "encoder.onnx"),
                    decoder_path=os.path.join(models_dir, "decoder.onnx"),
                    tokenizer_json=os.path.join(models_dir, "tokenizer.json")
                )
                print("✅ LaTeX OCR model initialized successfully!")
            except Exception as e:
                print(f"❌ Model initialization failed: {e}")
        else:
            print("❌ Model files not found")
    else:
        print("❌ Models directory not found")
else:
    print("❌ Import failed - LaTeX OCR functionality disabled")
