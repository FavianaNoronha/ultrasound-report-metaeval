#!/bin/bash

echo "=========================================="
echo "Medical Imaging AI - Quick Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "This may take several minutes..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To get started:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Read the README.md for next steps"
echo "3. Check docs/DATA_COLLECTION_GUIDE.md for data sources"
echo "4. Run: python src/orchestrator.py --help"
echo ""
echo "To test installation:"
echo "  python notebooks/01_setup_and_exploration.py"
echo ""
