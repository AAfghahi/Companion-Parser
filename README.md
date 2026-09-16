# Magic: The Gathering Tournament Standings Screenshot to CSV Converter

A Python utility that extracts Magic: The Gathering tournament standings from screenshots and converts them to CSV format with automatic match point calculation.

## Features

- **OCR-based extraction**: Automatically reads text from screenshot images using pytesseract
- **Match point calculation**: Calculates points based on Win-Loss-Draw match results
  - Win = 3 points
  - Loss = 0 points
  - Draw = 1 point
- **Round tracking**: Auto-detects current round/week or accepts explicit round number
- **Duplicate detection**: Merges multiple screenshots while removing duplicate player entries
- **CSV output**: Generates clean CSV files with Name, Record, Round, and Points columns

## Match Point Calculation

The script calculates match points from W-L-D (Win-Loss-Draw) records:
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
Convert a single round screenshot (uses current week's Monday as the week date):
```bash
python screenshot_to_csv.py standings.png -o tournament.csv
```

### Specify Week Start Date
```bash
python screenshot_to_csv.py standings.png -d 9/14/26 -o week.csv
```

### Multiple Rounds
Merge standings from multiple rounds (auto-removes duplicates):
```bash
python screenshot_to_csv.py round1.png round2.png round3.png -o all_rounds.csv
```

### Include OMW% Column
```bash
python screenshot_to_csv.py standings.png --omw -o standings.csv
```

### With Date and Multiple Files
```bash
python screenshot_to_csv.py round1.png round2.png -d 9/14/26 -o merged.csv
```

## Output Format

The generated CSV file contains:
- **name**: Player name
- **record**: Win-Loss-Draw record (e.g., "4-2-0")
- **week**: Week start date in M/D/YY format (Monday of that week)
- **points**: Calculated match points from the record
- **omw** (optional): Opposition Match Win percentage (if `--omw` flag used)

Example output:
```csv
name,record,week,points
Michael Ross,5-0-1,9/14/26,16
Ethan Riegle,5-1-0,9/14/26,15
Kora Benck,4-0-2,9/14/26,14
arash afghahi,4-2-0,9/14/26,12
```

## Command Line Options

```
-o, --output      Output CSV file path (default: standings.csv)
-d, --date        Week start date in M/D/YY format (default: current week Monday)
-s, --store       Store/event name for tracking (optional)
--json            Output JSON file path for artifact database (optional)
--omw             Include OMW% column in output
```

## JSON Output for Tracking Artifact

Generate JSON output for use with the standings tracking artifact:

```bash
python screenshot_to_csv.py standings.png -d 9/14/26 -s "Store Name" --json output.json
```

The JSON file can be imported into the tracking artifact for historical data aggregation and analysis.

## Duplicate Handling

When processing multiple round screenshots:
- Players appearing in multiple files are included only once
- The last occurrence of each player (by name, case-insensitive) is kept
- This is useful for removing duplicates from consecutive rounds or retakes

## Example Workflow

```bash
# Process standings from September 14, 2026
python screenshot_to_csv.py standings.png -d 9/14/26 -o week.csv

# Later, add another screenshot and merge
python screenshot_to_csv.py standings1.png standings2.png -d 9/14/26 -o merged.csv

# This will have all players from both screenshots, with no duplicates
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

## Magic: The Gathering Context

Magic: The Gathering uses match points to rank players during tournaments:
- **Match Win**: 3 points (player won the match 2-0 or 2-1)
- **Match Loss**: 0 points (player lost the match)
- **Match Draw**: 1 point (match ended in a draw)

The script extracts the W-L-D record from tournament standings screenshots and calculates the total match points for each player, which is useful for creating exportable records or aggregating data across multiple tournament rounds.

## Development

To modify the script:
- Point calculation logic: `calculate_points()` function
- OCR parsing: `parse_standings()` function
- CSV output: `write_csv()` function
