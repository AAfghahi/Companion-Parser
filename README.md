# Sports Standings Screenshot to CSV Converter

A Python utility that extracts sports standings data from screenshots and converts them to CSV format with automatic point calculation.

## Features

- **OCR-based extraction**: Automatically reads text from screenshot images using pytesseract
- **Point calculation**: Calculates points based on Win-Loss-Draw records
  - Win = 3 points
  - Loss = 0 points
  - Draw = 1 point
- **Week tracking**: Auto-detects current week or accepts explicit week number
- **Duplicate detection**: Merges multiple screenshots while removing duplicate player entries
- **CSV output**: Generates clean CSV files with Name, Record, Week, and Points columns

## Point Calculation

The script calculates points from W-L-D (Win-Loss-Draw) records:
- Format: `W-L-D` or `W-L` (draws optional)
- Examples:
  - `4-2-0` = (4×3) + (2×0) + (0×1) = 12 points
  - `5-1-2` = (5×3) + (1×0) + (2×1) = 17 points
  - `4-2` = (4×3) + (2×0) + (0×1) = 12 points

## Installation

### Requirements
- Python 3.7+
- Tesseract OCR engine

### System Setup

**macOS (Homebrew):**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
Convert a single screenshot:
```bash
python screenshot_to_csv.py screenshot.png -o standings.csv
```

### Specify Week Number
```bash
python screenshot_to_csv.py screenshot.png -w 5 -o week5.csv
```

### Multiple Screenshots
Merge multiple screenshots (auto-removes duplicates):
```bash
python screenshot_to_csv.py round1.png round2.png round3.png -o all_standings.csv
```

### Include OMW% Column
```bash
python screenshot_to_csv.py screenshot.png --omw -o standings.csv
```

### With Week and Multiple Files
```bash
python screenshot_to_csv.py img1.png img2.png -w 5 -o merged.csv
```

## Output Format

The generated CSV file contains:
- **name**: Player name
- **record**: Win-Loss-Draw record (e.g., "4-2-0")
- **week**: Week number
- **points**: Calculated points from the record
- **omw** (optional): Opposition Match Win percentage (if `--omw` flag used)

Example output:
```csv
name,record,week,points
Michael Ross,5-0-1,36,16
Ethan Riegle,5-1-0,36,15
Kora Benck,4-0-2,36,14
arash afghahi,4-2-0,36,12
```

## Command Line Options

```
-o, --output      Output CSV file path (default: standings.csv)
-w, --week        Week number (default: current ISO week)
--omw             Include OMW% column in output
```

## Duplicate Handling

When processing multiple screenshots:
- Players appearing in multiple files are included only once
- The last occurrence of each player (by name, case-insensitive) is kept
- This is useful for removing duplicates from consecutive rounds or retakes

## Example Workflow

```bash
# Process a single game round
python screenshot_to_csv.py round_5.png -o week5.csv

# Later, add another round and merge
python screenshot_to_csv.py round_5.png round_6.png -o rounds_5-6.csv

# This will have all players from both rounds, with no duplicates
```

## Troubleshooting

### "pytesseract.TesseractNotFoundError"
Tesseract OCR is not installed. Follow the system setup instructions above for your OS.

### Poor OCR Recognition
- Ensure the screenshot is clear and well-lit
- Try cropping to just the standings table
- Increase image resolution if possible

### Incorrect Point Calculation
Verify the record format is W-L-D or W-L with numbers separated by hyphens.

## Development

To modify the script:
- Point calculation logic: `calculate_points()` function
- OCR parsing: `parse_standings()` function
- CSV output: `write_csv()` function
