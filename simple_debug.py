#!/usr/bin/env python
"""
Simple debug for rapid_latex_ocr
"""

try:
    import rapid_latex_ocr
    print("Package imported successfully")
    print("Dir contents:", [x for x in dir(rapid_latex_ocr) if not x.startswith('_')])
    
    # Check if it's a function-based API instead of class-based
    if hasattr(rapid_latex_ocr, '__call__'):
        print("Package is callable")
    
    # Try to find any callable that might be the OCR function
    for name in dir(rapid_latex_ocr):
        attr = getattr(rapid_latex_ocr, name)
        if callable(attr) and not name.startswith('_'):
            print(f"Found callable: {name}")
            
except Exception as e:
    print(f"Error: {e}")

# Also try direct function import
try:
    from rapid_latex_ocr import latex_ocr
    print("Found latex_ocr function")
except:
    pass

try:
    from rapid_latex_ocr import rapid_latex_ocr as ocr_func
    print("Found rapid_latex_ocr function")
except:
    pass
