# Colorado Pauper Tournament Tracker - Setup Guide

This guide walks you through setting up a tournament tracking system similar to Colorado Pauper for your own Magic: The Gathering group.

## System Architecture

The system consists of three main components:

1. **Python OCR Script** (`screenshot_to_csv.py`) - Extracts tournament standings from screenshot images using Tesseract OCR
2. **Google Sheets + Apps Script** - Centralized data storage and backend API
3. **GitHub Pages Website** - Public-facing dashboard for viewing standings with multiple views (current season, historical seasons)

### Data Flow

```
Tournament Screenshot 
    ↓
Python OCR Script (extracts standings)
    ↓
Google Sheet (stores data)
    ↓
GitHub Pages Dashboard (displays standings)
```

## Prerequisites

Before starting, you'll need:

- A Google Account
- A GitHub Account
- Python 3.7+ installed locally
- Tesseract OCR installed on your machine
- A GitHub repository (create a new one or fork this one)
- A GitHub Pages enabled repository

## Step 1: Set Up Your Google Sheet

1. **Create a new Google Sheet**
   - Go to [sheets.google.com](https://sheets.google.com)
   - Click "Create" → "Spreadsheet"
   - Name it something like "Tournament Tracker - [Your Group Name]"

2. **Create your first sheet tab**
   - The default sheet should be named something like "Sheet1"
   - Rename it to match your current season (e.g., "Fall Season 2026")
   - Add headers: `Name`, `Record`, `Points`, `Week`
   
3. **For future seasons**
   - When a season ends, create a new sheet tab with the season name (e.g., "Winter Season 2026")
   - The main page will always read from "MTG Standings" (current season)
   - Historical pages will read from other named tabs

### Sheet Structure Example

| Name | Record | Points | Week |
|------|--------|--------|------|
| Alice | 4-2-0 | 12 | 9/14/26 |
| Bob | 3-2-1 | 10 | 9/14/26 |
| Carol | 5-1-0 | 15 | 9/21/26 |

## Step 2: Deploy Google Apps Script

1. **Open your Google Sheet**
   - Go to **Extensions** → **Apps Script**
   - A new tab will open with the script editor

2. **Copy the Apps Script code**
   - Replace everything in `Code.gs` with the contents of `mtg_tracker_apps_script.gs`
   - Save the script (Ctrl+S)

3. **Deploy as a web app**
   - Click **Deploy** → **New deployment**
   - Select type: **Web app**
   - Execute as: **Your email/account**
   - Who has access: **Anyone**
   - Click **Deploy**
   - Copy the deployment URL (you'll need this later)

### What This Script Does

- **GET requests** - Retrieves data from the current season sheet or a specific season
- **POST requests** - Allows appending new tournament data
- **listSeasons** - Lists all available season sheets for the history page

## Step 3: Set Up GitHub Pages

1. **Create/prepare your repository**
   - Create a new GitHub repository (or fork `aafghahi/Companion-Parser`)
   - Clone it locally: `git clone https://github.com/YOUR_USERNAME/tournament-tracker.git`
   - Create a `docs` folder if it doesn't exist

2. **Copy the HTML files**
   - Copy `index.html` (current season dashboard) to `docs/index.html`
   - Copy `season-history.html` (historical seasons) to `docs/season-history.html`
   - Update the `SCRIPT_URL` in both files with your Apps Script deployment URL

3. **Enable GitHub Pages**
   - Go to repository **Settings** → **Pages**
   - Under "Build and deployment", select source: **Deploy from a branch**
   - Branch: **main** (or your default branch)
   - Folder: **/docs**
   - Click **Save**

4. **Custom Domain (Optional)**
   - If you have a custom domain:
     - Create a file `docs/CNAME` with your domain name
     - Update your domain's DNS settings to point to GitHub Pages
     - See [GitHub Pages custom domain documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

## Step 4: Set Up Python OCR Script

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Required packages:
   - `Pillow` - Image processing
   - `pytesseract` - OCR text extraction
   - `openpyxl` - Excel file generation

2. **Install Tesseract OCR**
   
   **Windows:**
   - Download installer: https://github.com/UB-Mannheim/tesseract/wiki
   - Run installer, note the installation path
   - Add to PATH or specify in script

   **Mac:**
   ```bash
   brew install tesseract
   ```

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install tesseract-ocr
   ```

3. **Test the script**
   ```bash
   python screenshot_to_csv.py screenshot.png -o standings.xlsx -d 9/14/26
   ```

## Step 5: Customize for Your Group

### Update the HTML Titles and Branding

Edit `docs/index.html`:
- Change the `<title>` tag to your group name
- Update the `<h1>` header text
- Update the subtitle if desired

```html
<title>Your Group Name</title>
<h1>🧙‍♂️ Your Group Name</h1>
<p class="subtitle">Tournament standings</p>
```

### Update the Apps Script URL

In both `docs/index.html` and `docs/season-history.html`, find and replace:
```javascript
const SCRIPT_URL = 'YOUR_DEPLOYMENT_URL_HERE';
```

## Step 6: Managing Seasons

### Starting a New Season

1. **Rename current sheet**
   - In your Google Sheet, right-click the current "MTG Standings" tab
   - Rename to season name (e.g., "Fall Season 2026")

2. **Create new current season sheet**
   - Right-click and create a new sheet
   - Name it "MTG Standings"
   - Add headers: `Name`, `Record`, `Points`, `Week`

3. **Commit to GitHub**
   - Update version number if needed
   - Commit changes: `git add -A && git commit -m "Archive Fall Season 2026"`
   - Push: `git push origin main`

### Adding Tournament Data

1. **Take a screenshot** of the tournament standings
2. **Run the Python script**
   ```bash
   python screenshot_to_csv.py tournament_screenshot.png -d 9/21/26 -o standings.xlsx
   ```
3. **Open the Excel file** and copy the data
4. **Paste into Google Sheet** (current season's "MTG Standings" tab)
5. **Refresh the website** to see updated standings

## Step 7: Viewing Your Tracker

### Current Season Dashboard (`index.html`)
- Shows aggregated totals across all weeks
- Pagination: 10 players per page
- Search: Find players by name with autocomplete
- Filter: View top performers for a specific week

### Historical Seasons (`season-history.html`)
- Dropdown to select past seasons
- Final standings for each season
- Statistics (total entries, unique players, weeks tracked)

## Troubleshooting

### OCR Accuracy Issues

- **Blurry screenshots**: Take clearer photos of the standings
- **Emoji/special characters**: The script automatically removes non-alphabetic characters
- **Record parsing errors**: Ensure records are in W-L-D format (e.g., "4-2-0")

### Google Sheets Formatting

- **Dates converting to numbers**: Use the Excel output (.xlsx) and paste into Sheets
- **Records showing as dates**: The script quotes non-numeric fields to prevent auto-conversion

### Website Not Updating

- Check that the Apps Script deployment URL is correct in both HTML files
- Clear browser cache (Ctrl+Shift+Delete)
- Verify the Google Sheet tabs are named correctly

### GitHub Pages Not Working

- Ensure `/docs` folder has both HTML files
- Check that GitHub Pages is enabled in repository settings
- Wait a few minutes for changes to deploy (check Actions tab)

## Advanced Customization

### Changing the Leaderboard View

Edit `docs/index.html` in the `renderDashboard()` function to:
- Change pagination size (default: 10 per page)
- Modify how statistics are calculated
- Add additional table columns

### Modifying Excel Output

Edit `screenshot_to_csv.py` in the `write_excel()` function to:
- Change column widths
- Add formatting (colors, fonts)
- Include additional fields like OMW%

### Styling

Update the CSS in `docs/index.html` under the `<style>` tag:
- Change colors using CSS variables (`:root`)
- Modify fonts and sizes
- Update dark mode colors under `@media (prefers-color-scheme: dark)`

## Support & Questions

If you have issues:

1. **Check the logs**
   - Python script: Run with `-v` flag for verbose output
   - Google Apps Script: Check Logs (Ctrl+Enter)
   - Website: Open browser console (F12) for JavaScript errors

2. **Verify your data**
   - Test the Python script on a single screenshot
   - Manually check the Google Sheet data
   - Ensure proper date format (M/D/YY)

3. **Check permissions**
   - Google Apps Script: Verify "Execute as" is set to your account
   - GitHub Pages: Ensure `/docs` folder exists and is public
   - Python: Verify Tesseract is installed and in PATH

## Next Steps

Once set up, you can:

- Integrate with Discord for automated notifications
- Create a scoring API for programmatic access
- Add player profiles and historical stats
- Generate season reports and statistics

Enjoy tracking your tournaments!
