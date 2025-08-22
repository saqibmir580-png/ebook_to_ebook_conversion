#!/usr/bin/env python
"""
Download LaTeX OCR model files required for formula extraction
"""

import os
import requests
from pathlib import Path

# Model URLs from rapid-latex-ocr repository
MODEL_URLS = {
    "image_resizer.onnx": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/image_resizer.onnx",
    "encoder.onnx": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/encoder.onnx", 
    "decoder.onnx": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/decoder.onnx",
    "tokenizer.json": "https://github.com/RapidAI/RapidLatexOCR/releases/download/v0.0.0/tokenizer.json"
}

def download_file(url: str, filepath: str) -> bool:
    """Download a file from URL to filepath"""
    try:
        print(f"Downloading {os.path.basename(filepath)}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded {os.path.basename(filepath)}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {os.path.basename(filepath)}: {e}")
        return False

def download_models():
    """Download all required LaTeX OCR model files"""
    # Create models directory
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    print(f"Downloading LaTeX OCR models to {models_dir}")
    
    success_count = 0
    for filename, url in MODEL_URLS.items():
        filepath = models_dir / filename
        
        # Skip if file already exists
        if filepath.exists():
            print(f"⏭️  {filename} already exists, skipping")
            success_count += 1
            continue
            
        if download_file(url, str(filepath)):
            success_count += 1
    
    if success_count == len(MODEL_URLS):
        print(f"\n✅ All {len(MODEL_URLS)} model files downloaded successfully!")
        print("LaTeX OCR is now ready to use.")
    else:
        print(f"\n⚠️  Downloaded {success_count}/{len(MODEL_URLS)} files")
        print("Some downloads failed. Please check your internet connection and try again.")
    
    return success_count == len(MODEL_URLS)

if __name__ == "__main__":
    download_models()
