# MTG Tournament Tracker - Complete Guide

A complete system for tracking Magic: The Gathering tournament standings across multiple events and locations.

## System Overview

The system consists of two main components:

1. **Screenshot Parser** (`screenshot_to_csv.py`) - Extracts standings from tournament screenshots
2. **Tracking Artifact** - Web-based dashboard for aggregating and analyzing data

## Workflow

```
Tournament Screenshot
         ↓
    Parse with script
         ↓
   CSV + JSON output
         ↓
  Import to Tracker
         ↓
  View & Analyze
         ↓
  Export to Google Docs
```

## Step 1: Extract Data from Screenshots

### Basic Usage

```bash
python screenshot_to_csv.py standings.png -o standings.csv
```

### With Store and Date

```bash
python screenshot_to_csv.py standings.png \
  -d 9/14/26 \
  -s "Game Cafe Downtown" \
  -o week.csv \
  --json week.json
```

### Multiple Screenshots (Same Event)

```bash
python screenshot_to_csv.py round1.png round2.png round3.png \
  -d 9/14/26 \
  -s "Regional Championship" \
  -o tournament.csv \
  --json tournament.json
```

## Step 2: Import Data to Tracker

### Via JSON File (Recommended)

1. Go to the **Tracking Artifact** dashboard
2. Click the **Import Data** tab
3. Click **Upload JSON or CSV File**
4. Select your `.json` file
5. Click **Import Data**

### Via Copy-Paste

1. Click **Import Data** tab
2. In the **Paste JSON/CSV data** field, paste your JSON or CSV
3. Click **Import Data**

### Example JSON Format

```json
[
  {
    "name": "Player Name",
    "record": "4-2-0",
    "week": "9/14/26",
    "points": 12,
    "store": "Game Cafe Downtown"
  },
  {
    "name": "Another Player",
    "record": "5-1-0",
    "week": "9/14/26",
    "points": 15,
    "store": "Game Cafe Downtown"
  }
]
```

## Step 3: View & Analyze

### Dashboard Tab

- **Weekly Leaderboard**: See standings for each week and store
- **Top Performers**: View all-time player rankings across tournaments
- Filter by specific weeks or stores

### History Tab

- Select a participant
- View their complete tournament history
- Track performance over time

## Step 4: Export to Google Docs

### Formatted Table (Copy-Paste)

1. Go to **Export & Copy** tab
2. (Optional) Filter by week or store
3. Click **Generate Formatted Table**
4. Click **Copy to Clipboard**
5. Paste directly into your Google Docs

### CSV Export

1. Click **Download CSV** to get a spreadsheet file
2. Import into Google Sheets for calculations and charts

### JSON Export

1. Click **Download JSON** to save data
2. Use for backups or further processing

## Recurring Weekly Workflow

### Monday (After Tournament)

```bash
# Extract results from all store screenshots
python screenshot_to_csv.py store1_final.png store2_final.png store3_final.png \
  -d "$(date +%m/%d/%y -d 'last monday')" \
  -s "Store Name" \
  --json weekly_results.json
```

### Wednesday (Aggregation)

1. Collect JSON files from all stores
2. Import to tracking artifact
3. View combined leaderboards

### Friday (Reporting)

1. Go to tracking artifact
2. Export & Copy formatted table
3. Paste into weekly update Google Doc

## Command Reference

```bash
python screenshot_to_csv.py [images] [options]

Positional:
  images                    Screenshot image file(s) to process

Options:
  -o, --output FILE        Output CSV file (default: standings.csv)
  -d, --date DATE          Week start date in M/D/YY format
  -s, --store NAME         Store/event name for tracking
  --json FILE              Export as JSON for artifact
  --omw                    Include Opposition Match Win percentage
```

## Tips & Tricks

### Multiple Events Per Week

Tag each store with a unique identifier:

```bash
python screenshot_to_csv.py fri_standings.png \
  -s "Downtown Friday" \
  -d 9/14/26 \
  --json friday.json

python screenshot_to_csv.py sat_standings.png \
  -s "Mall Saturday" \
  -d 9/14/26 \
  --json saturday.json
```

Then import both JSON files to the tracker.

### Batch Processing Script

Create `process_week.sh`:

```bash
#!/bin/bash
WEEK_DATE="$1"  # e.g., "9/14/26"

python screenshot_to_csv.py \
  store1_standings.png \
  -d "$WEEK_DATE" \
  -s "Store 1" \
  --json store1.json

python screenshot_to_csv.py \
  store2_standings.png \
  -d "$WEEK_DATE" \
  -s "Store 2" \
  --json store2.json

echo "Week $WEEK_DATE processed. Import JSON files to tracker."
```

Usage:
```bash
chmod +x process_week.sh
./process_week.sh 9/14/26
```

### Backup Your Data

Regularly export JSON to keep backups:

1. Go to **Manage** tab
2. Note the statistics
3. Go to **Export & Copy**
4. Click **Download JSON**
5. Store in a safe location (Google Drive, etc.)

## Database Features

### Data Persistence

All data is stored in your browser's IndexedDB database:
- Persists across browser sessions
- Private to your browser
- No data sent to external servers

### Clear Data

To start fresh:

1. Go to **Manage** tab
2. Click **Clear All Data**
3. Confirm when prompted

⚠️ **Warning:** This cannot be undone!

## Troubleshooting

### Import Not Working

- Verify JSON/CSV format is correct
- Check that all required fields are present:
  - `name`
  - `record` (e.g., "4-2-0")
  - `week` (e.g., "9/14/26")
  - `points` (number)
  - `store` (optional but recommended)

### Duplicate Entries

- The system doesn't automatically deduplicate
- If you import the same data twice, use the **Manage** tab to clear and re-import

### Export Quality Issues

- For best results in Google Docs, use the "Formatted Table" copy-paste option
- Tab-separated values maintain alignment when pasted
- Alternatively, import CSV to Google Sheets first, then embed/reference in Docs

## Advanced: Automating with Your Own Tools

### Python

```python
import json
import subprocess

# Generate JSON from screenshots
result = subprocess.run([
    'python', 'screenshot_to_csv.py',
    'standings.png',
    '-d', '9/14/26',
    '-s', 'My Store',
    '--json', 'output.json'
], capture_output=True)

# Read the JSON
with open('output.json') as f:
    data = json.load(f)

# Process further if needed
for entry in data:
    entry['custom_field'] = 'value'
```

### Google Sheets API

If you want to automate Google Sheets updates:

```python
# This would require setting up Google Sheets API credentials
# Then you could push data directly to a spreadsheet
# See: https://developers.google.com/sheets/api
```

## Support

For issues with:
- **Screenshot parsing**: Check that images are clear and properly cropped
- **OCR accuracy**: Ensure text is legible; try higher resolution images
- **Artifact features**: Use the artifact's import/export tools to verify data format

## Updates

The tracking artifact is updated automatically. No installation needed beyond the initial bookmark.
