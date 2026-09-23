# PaddleOCR Installation Guide for Windows

This guide helps you get PaddleOCR installed on Windows for superior colored row extraction in the screenshot OCR tool.

## Why PaddleOCR?

- **Tesseract** extracts only ~4 entries from colored row screenshots (unreliable)
- **PaddleOCR** extracts ~14+ entries from the same screenshots (robust)
- PaddleOCR is specifically designed to handle colored text on colored backgrounds

## Prerequisites

- Python 3.8 or later
- Administrator access (for some installation methods)

## Installation Methods (Recommended Order)

### Method 1: Conda (RECOMMENDED - Easiest)

If you have Conda/Anaconda installed, this is the simplest path:

```powershell
# Activate your environment (if using conda)
conda activate your_env

# Install PaddleOCR
conda install -c conda-forge paddleocr

# Verify installation
python -c "from paddleocr import PaddleOCR; print('PaddleOCR installed successfully')"
```

**Why Conda?** Pre-built binaries avoid the PyYAML compilation issue entirely.

### Method 2: pip with Visual C++ Build Tools

If you don't have Conda, first ensure C++ build tools are installed:

1. **Install Visual Studio Build Tools:**
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - During installation, select "Desktop development with C++"
   - Complete the installation

2. **Then install PaddleOCR:**

```powershell
# Upgrade pip, setuptools, and wheel
python -m pip install --upgrade pip setuptools wheel

# Install PaddleOCR
pip install paddlepaddle paddleocr

# Verify installation
python -c "from paddleocr import PaddleOCR; print('PaddleOCR installed successfully')"
```

### Method 3: Windows Subsystem for Linux (WSL2)

If the above methods fail, WSL2 provides a Linux environment on Windows where installation is trivial:

1. **Enable WSL2:**
   ```powershell
   wsl --install
   # Restart your computer
   ```

2. **In WSL2 terminal:**
   ```bash
   sudo apt update
   sudo apt install python3-pip
   pip3 install paddleocr
   ```

3. **Run the OCR script in WSL2:**
   ```bash
   cd /mnt/c/path/to/Companion-Parser
   python3 screenshot_to_csv.py Screenshots/9.14.26.EG.png -d "9/14/26"
   ```

## Troubleshooting

### Error: "Microsoft Visual C++ 14.0 or greater is required"

This means PyYAML compilation failed. Solutions:
1. Try **Method 1 (Conda)** - bypasses this entirely
2. Install Visual Studio Build Tools (see Method 2)
3. Use **Method 3 (WSL2)**

### Error: "ModuleNotFoundError: No module named 'paddlex'"

After installation, this error might occur. Try:
```powershell
pip install paddlex --upgrade
```

### Error: "No module named 'paddleocr'"

The installation didn't complete successfully. Try:
```powershell
# Uninstall and reinstall
pip uninstall paddleocr paddlepaddle -y
pip install paddleocr  # Let it auto-install paddlepaddle
```

## Fallback: Tesseract

If PaddleOCR installation remains problematic, the script automatically falls back to Tesseract. This will extract fewer entries from colored rows but still works:

```powershell
# Ensure Tesseract is installed
python -m pip install pytesseract

# Run the script (will use Tesseract if PaddleOCR unavailable)
python screenshot_to_csv.py Screenshots/9.14.26.EG.png
```

## Testing Your Installation

After installation, verify it works:

```powershell
# Quick test
python -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(); print('✓ PaddleOCR ready')"

# Full test with actual screenshot
python screenshot_to_csv.py Screenshots/9.14.26.EG.png -d "9/14/26"
```

If successful, you should see 14-16 entries extracted (vs. 4 with Tesseract).

## Performance Notes

- **First run:** PaddleOCR downloads models (~100MB) - this takes 1-2 minutes
- **Subsequent runs:** Instant, models cached locally
- **CPU-only:** ~10-15 seconds per screenshot
- **GPU optional:** Install CUDA for faster processing (advanced)

## Questions?

If installation fails after trying all methods, the script will automatically fall back to Tesseract. Report issues with detailed error messages for further assistance.
