# Quick Start Guide: Setting Up Your MTG Tournament Tracker

**For: Your Minnesota Magic Group**

Hey! This is a simplified guide to get your tournament tracker running in about 30 minutes. Follow these steps in order.

## What You're Setting Up

A free website that:
- Shows current season tournament standings
- Lets you view past seasons
- Auto-updates when you add new tournament data
- Looks professional and works on phones/tablets

## Step 1: Prep Work (5 minutes)

You'll need:
- [ ] Google Account (Gmail works)
- [ ] GitHub Account (free at github.com)
- [ ] Python 3.7+ installed on your computer
- [ ] Tesseract OCR (instructions below)

### Install Tesseract OCR

**Windows:**
1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
2. Click the latest installer (current: `tesseract-ocr-w64-setup-v5.x.exe`)
3. Run it, keep all defaults, note the install path
4. Done!

**Mac:**
```bash
brew install tesseract
```

**Linux (Ubuntu):**
```bash
sudo apt-get install tesseract-ocr
```

## Step 2: Create Your Google Sheet (5 minutes)

1. Go to [sheets.google.com](https://sheets.google.com)
2. Click **Create** → **Spreadsheet**
3. Name it: "Minnesota Magic Tracker" (or whatever you want)
4. Rename the default sheet to: "MTG Standings"
5. Add these headers in the first row:
   - A1: `Name`
   - B1: `Record`
   - C1: `Points`
   - D1: `Week`

That's it! Leave it empty for now, we'll add data later.

## Step 3: Deploy Google Apps Script (5 minutes)

1. In your Google Sheet, go to **Extensions** → **Apps Script**
2. Delete the existing code in `Code.gs`
3. Copy this entire script and paste it:

```javascript
// MTG Tournament Tracker - Google Apps Script Backend
const SHEET_NAME = 'MTG Standings';

function initializeSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(['Name', 'Record', 'Points', 'Week', 'Store', 'Timestamp']);
  }
  return sheet;
}

function doGet(e) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  if (e.parameter && e.parameter.season) {
    const seasonName = e.parameter.season;
    const sheet = ss.getSheetByName(seasonName);
    if (!sheet) {
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        message: 'Season not found: ' + seasonName
      })).setMimeType(ContentService.MimeType.JSON);
    }
    const data = sheet.getDataRange().getValues();
    return ContentService.createTextOutput(JSON.stringify(data))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  if (e.parameter && e.parameter.listSeasons) {
    const sheets = ss.getSheets();
    const seasonNames = sheets.map(sheet => sheet.getName());
    return ContentService.createTextOutput(JSON.stringify(seasonNames))
      .setMimeType(ContentService.MimeType.JSON);
  }
  
  const sheet = initializeSheet();
  const data = sheet.getDataRange().getValues();
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const sheet = initializeSheet();
    const payload = JSON.parse(e.postData.contents);

    if (payload.action === 'append') {
      const rows = payload.data;
      rows.forEach(row => {
        sheet.appendRow([
          row.name || '',
          row.record || '',
          row.points || 0,
          row.week || '',
          row.store || '',
          new Date().toISOString()
        ]);
      });
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: 'Data imported: ' + rows.length + ' entries'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    if (payload.action === 'clear') {
      if (sheet.getMaxRows() > 1) {
        sheet.deleteRows(2, sheet.getMaxRows() - 1);
      }
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: 'Sheet cleared'
      })).setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      message: 'Unknown action'
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
```

4. Click **Save** (Ctrl+S)
5. Click **Deploy** → **New deployment**
6. Select: **Type** → **Web app**
7. **Execute as:** Your email
8. **Who has access:** Anyone
9. Click **Deploy**
10. **IMPORTANT:** Copy the deployment URL and save it somewhere (you'll need it)

## Step 4: Create GitHub Repo (5 minutes)

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `minnesota-magic-tracker`
3. Add description: "Tournament tracker for Minnesota Magic group"
4. Choose **Public** (so website is accessible)
5. Click **Create repository**
6. Don't add README or gitignore yet, just create it

## Step 5: Set Up Your Website Files (5 minutes)

1. Clone your repo locally:
```bash
git clone https://github.com/YOUR_USERNAME/minnesota-magic-tracker.git
cd minnesota-magic-tracker
```

2. Create the folder structure:
```bash
mkdir docs
```

3. Create `docs/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minnesota Magic Tracker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --text-primary: #1a1a1a;
            --text-secondary: #666666;
            --border: #e0e0e0;
            --accent: #6366f1;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #1a1a1a;
                --bg-secondary: #2d2d2d;
                --text-primary: #ffffff;
                --text-secondary: #b0b0b0;
                --border: #404040;
                --accent: #818cf8;
            }
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header { margin-bottom: 30px; border-bottom: 2px solid var(--border); padding-bottom: 20px; }
        h1 { font-size: 2em; margin-bottom: 10px; }
        .subtitle { color: var(--text-secondary); font-size: 0.95em; }
        h2 { margin-top: 30px; margin-bottom: 20px; }
        .filter-section {
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filter-section label { font-weight: 500; }
        .filter-section select, .filter-section input {
            min-width: 150px;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-size: 1em;
        }
        .table-container { overflow-x: auto; margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; background: var(--bg-secondary); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border); }
        th { font-weight: 600; color: var(--accent); }
        tr:hover { background: var(--bg-primary); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧙‍♂️ Minnesota Magic Tracker</h1>
            <p class="subtitle">Current season tournament standings</p>
        </header>

        <div class="filter-section">
            <label for="weekFilter">Filter by Week:</label>
            <select id="weekFilter">
                <option value="">All Weeks (Totals)</option>
            </select>
            <label for="searchPlayer">Search:</label>
            <input type="text" id="searchPlayer" placeholder="Enter player name..." list="playerNames">
            <datalist id="playerNames"></datalist>
        </div>

        <h2>Leaderboard</h2>
        <div class="table-container">
            <table id="leaderboard">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Player</th>
                        <th>Total Points</th>
                        <th>Tournaments</th>
                        <th>Avg Points</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <script>
        const SCRIPT_URL = 'YOUR_APPS_SCRIPT_URL_HERE'; // Replace with your deployment URL

        function formatDate(dateValue) {
            if (!dateValue) return '';
            if (typeof dateValue === 'string' && /^\d{1,2}\/\d{1,2}\/\d{2,4}$/.test(dateValue)) {
                return dateValue;
            }
            let date;
            if (typeof dateValue === 'string' && dateValue.includes('T')) {
                date = new Date(dateValue);
            } else if (typeof dateValue === 'number') {
                date = new Date(dateValue);
            } else if (dateValue instanceof Date) {
                date = dateValue;
            } else {
                return String(dateValue);
            }
            if (isNaN(date.getTime())) return String(dateValue);
            const month = date.getMonth() + 1;
            const day = date.getDate();
            const year = date.getFullYear().toString().slice(-2);
            return `${month}/${day}/${year}`;
        }

        async function loadData() {
            try {
                const response = await fetch(SCRIPT_URL);
                const rows = await response.json();
                renderDashboard(rows);
                populateFilters(rows);
            } catch (error) {
                console.error('Error:', error);
                document.querySelector('#leaderboard tbody').innerHTML = 
                    '<tr><td colspan="5" style="text-align: center;">Error loading data</td></tr>';
            }
        }

        function renderDashboard(rows) {
            if (rows.length <= 1) {
                document.querySelector('#leaderboard tbody').innerHTML = 
                    '<tr><td colspan="5" style="text-align: center;">No data yet</td></tr>';
                return;
            }

            const weekFilter = document.getElementById('weekFilter').value;
            const searchTerm = document.getElementById('searchPlayer').value.toLowerCase();

            const playerStats = {};
            rows.slice(1).forEach(row => {
                const name = row[0];
                const points = parseInt(row[2]) || 0;
                const week = row[3] || '';
                
                if (!playerStats[name]) {
                    playerStats[name] = { total: 0, count: 0, entries: [] };
                }
                playerStats[name].total += points;
                playerStats[name].count += 1;
                playerStats[name].entries.push({ points, week });
            });

            let leaderboardData = Object.entries(playerStats)
                .map(([name, stats]) => ({
                    name,
                    total: stats.total,
                    count: stats.count,
                    avg: Math.round(stats.total / stats.count),
                    entries: stats.entries
                }));

            if (weekFilter) {
                leaderboardData = leaderboardData
                    .map(player => ({
                        ...player,
                        weekTotal: player.entries.filter(e => e.week === weekFilter).reduce((sum, e) => sum + e.points, 0),
                        weekCount: player.entries.filter(e => e.week === weekFilter).length
                    }))
                    .filter(player => player.weekCount > 0)
                    .sort((a, b) => b.weekTotal - a.weekTotal);
            } else {
                leaderboardData.sort((a, b) => b.total - a.total);
            }

            if (searchTerm) {
                leaderboardData = leaderboardData.filter(p => p.name.toLowerCase().includes(searchTerm));
            }

            const tbody = document.querySelector('#leaderboard tbody');
            tbody.innerHTML = leaderboardData.map((player, idx) => `
                <tr>
                    <td>${idx + 1}</td>
                    <td>${player.name}</td>
                    <td><strong>${weekFilter ? player.weekTotal : player.total}</strong></td>
                    <td>${weekFilter ? player.weekCount : player.count}</td>
                    <td>${weekFilter ? (player.weekCount > 0 ? (player.weekTotal / player.weekCount).toFixed(1) : '0') : player.avg}</td>
                </tr>
            `).join('');
        }

        function populateFilters(rows) {
            const weeks = new Set(rows.slice(1).map(r => r[3]).filter(Boolean));
            const weekSelect = document.getElementById('weekFilter');
            weekSelect.innerHTML = '<option value="">All Weeks</option>' +
                Array.from(weeks).sort().reverse().map(w =>
                    `<option value="${w}">${formatDate(w)}</option>`
                ).join('');

            const playerNames = new Set(rows.slice(1).map(r => r[0]).filter(Boolean));
            const datalist = document.getElementById('playerNames');
            datalist.innerHTML = Array.from(playerNames).sort().map(name =>
                `<option value="${name}"></option>`
            ).join('');
        }

        document.getElementById('weekFilter').addEventListener('change', () => loadData());
        document.getElementById('searchPlayer').addEventListener('input', () => loadData());

        window.addEventListener('load', () => loadData());
        setInterval(() => loadData(), 30000);
    </script>
</body>
</html>
```

4. Replace `YOUR_APPS_SCRIPT_URL_HERE` with your Apps Script deployment URL from Step 3

5. Commit and push:
```bash
git add docs/index.html
git commit -m "Add tournament tracker dashboard"
git push origin main
```

## Step 6: Enable GitHub Pages (3 minutes)

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/docs**
4. Click **Save**
5. Wait 1-2 minutes, then visit `https://YOUR_USERNAME.github.io/minnesota-magic-tracker/`

That's it! Your website is live! 🎉

## Step 7: Add Your First Tournament Data

1. Take a screenshot of the tournament standings (from MTG Companion or however you track it)
2. Download the Python script from this repo
3. Run:
```bash
python screenshot_to_csv.py tournament_screenshot.png -d 9/21/26 -o standings.xlsx
```

4. Open the generated Excel file
5. Copy the data (rows with player names, records, points)
6. Go to your Google Sheet and paste it into "MTG Standings" sheet
7. Refresh your website - it should show the data!

## Adding More Tournaments

Each tournament:
1. Screenshot the standings
2. Run the Python script with new date
3. Copy data to Google Sheet
4. Website auto-updates in seconds

## Customizing Your Site

### Change the Name
Edit `docs/index.html`:
- Line with `<title>` tag
- Line with `<h1>` tag

### Change the Google Apps Script URL
In `docs/index.html`, find `SCRIPT_URL = 'YOUR_APPS_SCRIPT_URL_HERE'` and update

### Change Colors
In `docs/index.html`, look for `:root {` section and modify:
- `--accent: #6366f1;` (blue) - change to your favorite color

## Troubleshooting

**Website shows "Error loading data"**
- Check that SCRIPT_URL is correct in the HTML
- Make sure Apps Script deployment URL is copied exactly
- Verify the script was deployed as a web app

**OCR not working**
- Make sure Tesseract is installed
- On Windows, may need to add to PATH or specify in script
- Try: `python screenshot_to_csv.py --help`

**Data not showing up**
- Verify data is in Google Sheet
- Check that sheet tab is named "MTG Standings"
- Try refreshing website (Ctrl+Shift+R to clear cache)

## Next Steps

Once this is working, you can:
- Add past season tabs (just create new sheets with season names)
- Customize colors and styling
- Add Discord notifications
- Share the website URL with your group!

---

**Questions?** Check the full SETUP_GUIDE.md for more detailed explanations of each step.

Good luck! 🧙‍♂️
