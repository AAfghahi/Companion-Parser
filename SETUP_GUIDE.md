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

### Script Features

The OCR script automatically:
- Extracts player names, records, points, and OMW% from screenshots
- Calculates match points (Win = 3 points, Draw = 1 point, Loss = 0 points)
- Includes OMW% column in output by default
- Generates Excel files for easy copying into Google Sheets
- Removes emojis and special characters from player names

**Command examples:**
```bash
# Basic usage with date
python screenshot_to_csv.py screenshot.png -d 9/14/26 -o standings.xlsx

# Multiple screenshots (merged with duplicates removed)
python screenshot_to_csv.py img1.png img2.png -o standings.xlsx

# Without OMW% column (optional)
python screenshot_to_csv.py screenshot.png --no-omw -o standings.xlsx
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
- **Weekly Scores Table**: Shows each player's score for the most recent week
- **Leaderboard**: Shows aggregated totals across all weeks
- **Pagination**: 10 players per page on both tables
- **Search**: Find players by name with autocomplete
- **Filter**: View top performers for a specific week

### Historical Seasons (`season-history.html`)
- **Season Selector**: Dropdown to view any archived season
- **Week Filter**: Filter standings to show only a specific week
- **Player Search**: Search for specific players with autocomplete
- **Final Standings**: Displays leaderboard with OMW% as tiebreaker
- **Statistics**: Shows total entries, unique players, and weeks tracked for each season

## Step 8: Optional - Set Up Score Discrepancy Reporting with Discord

The dashboard includes a built-in "Report Score Discrepancy" feature that allows users to report potential scoring errors. These reports can be automatically sent to your Discord server.

### Setting Up Discord Webhooks

1. **Create a Discord Server Channel** (or use existing)
   - Go to your Discord server
   - Create a new channel (e.g., #tournament-reports) or use an existing one
   - Make sure the bot has permission to post messages

2. **Create a Webhook**
   - Right-click the channel → **Edit Channel**
   - Go to **Integrations** → **Webhooks**
   - Click **New Webhook**
   - Name it something like "Tournament Tracker"
   - Click **Copy Webhook URL** and save it

3. **Update the HTML File**
   - Open `docs/index.html` in a text editor
   - Find the line with `fetch('https://discord.com/api/webhooks/...`
   - Replace the entire URL with your webhook URL:
   ```javascript
   fetch('YOUR_DISCORD_WEBHOOK_URL_HERE', {
   ```

4. **Commit and push the change**
   ```bash
   git add docs/index.html
   git commit -m "Add Discord webhook URL for score reports"
   git push origin main
   ```

### How Users Report Discrepancies

1. On the dashboard, click the **"Report Score Discrepancy"** button
2. A form appears with fields for:
   - **Your Name** (dropdown of all players)
   - **Week** (dropdown of available weeks)
   - **Current Score Shown** (auto-filled based on selected player/week)
   - **Expected Score** (what it should be)
   - **Reason** (explanation of the error)
   - **Contact Info** (optional - email or Discord username)

3. Click **Submit Report**
4. The report is stored locally and sent to your Discord channel
5. A success message confirms the submission

### Discord Message Format

Reports appear in Discord as formatted embeds showing:
- Player name
- Tournament week
- Current and expected scores
- Reason for discrepancy
- Submitter contact information
- Timestamp

### Troubleshooting Discord Integration

If reports don't appear in Discord:

1. **Check the browser console** (F12)
   - Look for error messages about the webhook
   - Common error: 404 (webhook URL is wrong or expired)

2. **Verify webhook URL**
   - Make sure the full URL was copied correctly
   - Check that the webhook hasn't been deleted in Discord

3. **Check Discord permissions**
   - Ensure the webhook has permission to post messages
   - Verify the channel is accessible

4. **Webhook expiration**
   - Discord webhooks can expire; create a new one if reports stop working
   - Keep a backup of your webhook URL

## Performance Features

### Browser Caching
The website automatically caches data locally in your browser with a 5-minute expiration:
- **Faster page loads**: Switching between tabs loads cached data instantly
- **Offline access**: If the API is temporarily unavailable, cached data is still shown
- **Automatic refresh**: After 5 minutes, fresh data is fetched from the server
- **Reduced server load**: Less frequent API calls to Google Apps Script

This caching is automatic and requires no configuration.

### OMW% (Opponent Match Win) Tiebreaker
When players have equal points in the leaderboard:
- Primary sort: Total points (highest first)
- Secondary sort: OMW% (highest first)
- This gives credit to players who faced stronger opponents

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

- **Set up Discord score discrepancy reporting** (see Step 8 above)
- Create a scoring API for programmatic access
- Add player profiles and historical stats
- Generate season reports and statistics
- Automate tournament data import with webhooks

Enjoy tracking your tournaments!
