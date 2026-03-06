# Getting Started with Medical Imaging AI

## 🎯 Quick Start Guide

### Step 1: Environment Setup (5 minutes)

```bash
# Navigate to project
cd medical-imaging-ai

# Run automated setup (recommended)
./setup.sh

# OR manual setup:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
# Test the installation
python notebooks/01_setup_and_exploration.py
```

Expected output:
```
✅ PyTorch: 2.x.x
✅ pydicom: 2.x.x
✅ NumPy: 1.x.x
✅ Pillow installed
```

### Step 3: Understand the System

Read these documents in order:
1. **README.md** - Project overview
2. **docs/DATA_COLLECTION_GUIDE.md** - How to get medical imaging data
3. **docs/AI_AGENT_ARCHITECTURE.md** - System architecture

### Step 4: Get Data (Choose one path)

#### Path A: Quick Testing (Recommended for beginners)
```bash
# Download sample chest X-ray dataset from NIH
# Visit: https://nihcc.app.box.com/v/ChestXray-NIHCC
# Download a small subset (e.g., 1000 images)
# Place in: data/raw/images/
```

#### Path B: Production Dataset (Recommended for serious development)
```bash
# Apply for MIMIC-CXR access
# 1. Go to: https://physionet.org/
# 2. Create account
# 3. Complete CITI training: https://about.citiprogram.org/
# 4. Apply for MIMIC-CXR dataset
# 5. Wait for approval (usually 1-2 weeks)
# 6. Download dataset (~500GB)
```

### Step 5: Run Your First Analysis

#### Option A: Using Python API

Create a file `test_pipeline.py`:

```python
from src.orchestrator import MedicalImagingOrchestrator

# Initialize the AI system
orchestrator = MedicalImagingOrchestrator()

# Process a single medical image
result = orchestrator.process_image(
    "data/raw/images/your_xray.dcm",
    output_dir="data/reports",
    save_report=True
)

# Print the report
print(result['report'])

# Check findings
print(f"\nNumber of findings: {result['num_findings']}")
print(f"Risk level: {result['risk_level']}")
```

Run it:
```bash
python test_pipeline.py
```

#### Option B: Using Command Line

```bash
# Process single image with text report
python src/orchestrator.py \
    --image data/raw/images/sample.dcm \
    --output data/reports \
    --format text

# Process batch of images with JSON output
python src/orchestrator.py \
    --batch data/raw/images/ \
    --output data/reports \
    --format json
```

### Step 6: Review Output

The system generates:

1. **Text Report** (data/reports/sample_report.txt):
```
============================================================
RADIOLOGY REPORT
============================================================

PATIENT INFORMATION:
  Patient ID: P12345
  Study Date: 2026-03-06
  Modality: X-RAY
  Body Part: CHEST

FINDINGS:
  1. Airspace opacity in right lower lobe...
  
IMPRESSION:
  Findings consistent with pneumonia
```

2. **JSON Report** (for programmatic use):
```json
{
  "report_id": "RPT_20260306_143022",
  "findings": [...],
  "impression": {...}
}
```

## 🔧 Common Issues & Solutions

### Issue 1: "CUDA not available"
**Solution**: System will use CPU (slower but works). To use GPU, install CUDA-enabled PyTorch:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Issue 2: "pydicom: Cannot read DICOM file"
**Solution**: Ensure file is valid DICOM format. Test with:
```python
import pydicom
dcm = pydicom.dcmread("your_file.dcm")
print(dcm)
```

### Issue 3: "Out of memory"
**Solution**: Reduce batch size or process images one at a time.

### Issue 4: "No module named 'src'"
**Solution**: Make sure you're in the project root directory:
```bash
cd medical-imaging-ai
python -c "import src; print('OK')"
```

## 📊 Example Workflow

### Complete Example: Processing a Chest X-ray

```python
from src.orchestrator import MedicalImagingOrchestrator
import os

# 1. Initialize system
print("Initializing AI system...")
orchestrator = MedicalImagingOrchestrator(
    vision_model="resnet50",
    confidence_threshold=0.5
)

# 2. Process image
print("Processing X-ray...")
result = orchestrator.process_image(
    "data/raw/images/chest_xray_001.dcm",
    output_dir="data/reports",
    save_report=True,
    report_format='text'
)

# 3. Analyze results
print(f"\n{'='*60}")
print("ANALYSIS SUMMARY")
print(f"{'='*60}")
print(f"Risk Level: {result['risk_level'].upper()}")
print(f"Findings: {result['num_findings']}")

# 4. Display findings
if result['num_findings'] > 0:
    print("\nDetailed Findings:")
    for i, finding in enumerate(result['analysis_results']['findings'], 1):
        print(f"{i}. {finding['condition']}")
        print(f"   Confidence: {finding['confidence']*100:.1f}%")
        print(f"   Severity: {finding['severity']}")
        print(f"   Location: {finding['location']}")

# 5. View full report
print(f"\n{'='*60}")
print("FULL RADIOLOGY REPORT")
print(f"{'='*60}")
print(result['report'])
```

## 🚀 Next Steps

After completing the quick start:

1. **Explore the code**:
   - `src/agent/vision_agent.py` - Image processing
   - `src/agent/analysis_agent.py` - Disease detection
   - `src/agent/report_agent.py` - Report generation

2. **Customize for your needs**:
   - Modify disease classes in `analysis_agent.py`
   - Adjust confidence thresholds
   - Customize report templates

3. **Train your own models**:
   - See `notebooks/` for training examples
   - Fine-tune on your specific data

4. **Advanced features**:
   - Integrate GPT-4 for better reports
   - Add custom segmentation models
   - Build web interface

## 📚 Learning Path

### Beginner (Week 1):
- ✅ Set up environment
- ✅ Download sample data
- ✅ Run basic pipeline
- Learn about medical imaging formats (DICOM)

### Intermediate (Weeks 2-4):
- Understand the agent architecture
- Modify existing agents
- Train simple classifiers
- Evaluate performance

### Advanced (Weeks 5+):
- Fine-tune vision models
- Implement custom segmentation
- Integrate advanced LLMs
- Clinical validation

## 🆘 Getting Help

1. Check documentation in `docs/`
2. Review code comments
3. Read error messages carefully
4. Search for similar issues online

## ⚠️ Important Reminders

- This is for **research/education only**
- Not approved for **clinical use**
- Always **validate AI outputs**
- Follow **data use agreements**
- Respect patient **privacy** (use de-identified data only)

---

**You're ready to start!** 🎉

Begin with Step 1 above and work through each step systematically.
