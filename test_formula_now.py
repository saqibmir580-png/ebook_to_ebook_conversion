#!/usr/bin/env python
"""
Test formula conversion after creating the file
"""

try:
    from app.utils.formula_converter import formula_converter
    print("✅ Formula converter imported successfully")
    
    # Test basic conversions
    test_cases = [
        r"\frac{1}{2}",
        r"x^2 + y^2",
        r"\alpha + \beta",
        r"\int x dx",
        r"\sum_{i=1}^n x_i",
        r"E = mc^2",
        r"\pi \approx 3.14159"
    ]
    
    print("\n🧪 Testing formula conversions:")
    print("=" * 40)
    
    for latex in test_cases:
        readable = formula_converter.convert_to_readable(latex)
        print(f"LaTeX:    {latex:20}")
        print(f"Readable: {readable}")
        print("-" * 40)
        
    print("\n✅ All formula conversions completed!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
