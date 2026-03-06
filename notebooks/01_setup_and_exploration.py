"""
Example notebook setup and initial exploration
"""

# Installation check
print("🔧 Checking installations...")

try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   CUDA device: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("❌ PyTorch not installed. Run: pip install torch torchvision")

try:
    import pydicom
    print(f"✅ pydicom: {pydicom.__version__}")
except ImportError:
    print("❌ pydicom not installed. Run: pip install pydicom")

try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError:
    print("❌ NumPy not installed")

try:
    from PIL import Image
    print(f"✅ Pillow installed")
except ImportError:
    print("❌ Pillow not installed. Run: pip install Pillow")

print("\n" + "="*60)
print("📚 Medical Imaging AI - Setup Complete!")
print("="*60)
print("\nNext steps:")
print("1. Download sample medical images")
print("2. Place them in data/raw/images/")
print("3. Run the example pipeline")
print("\nSee README.md for detailed instructions.")
