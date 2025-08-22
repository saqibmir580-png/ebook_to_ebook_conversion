#!/usr/bin/env python
"""
Simple script to install correct rapid-latex-ocr version
"""

import subprocess
import sys

def install_packages():
    """Install rapid-latex-ocr with correct version"""
    packages = [
        "rapid-latex-ocr==0.0.9",
        "onnxruntime",
        "torch",
        "torchvision", 
        "numpy"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ {package} installed successfully")
            else:
                print(f"✗ Failed to install {package}: {result.stderr}")
        except Exception as e:
            print(f"✗ Error installing {package}: {e}")
    
    # Test import
    print("\nTesting import...")
    try:
        from rapid_latex_ocr import LatexOCR
        print("✓ rapid-latex-ocr imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

if __name__ == "__main__":
    install_packages()
