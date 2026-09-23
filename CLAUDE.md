# Companion Parser - Architecture & Development Guide

**Colorado Pauper MTG Tournament Tracker** — A real-time standings tracker with Google Sheets integration, Supabase database, and automated data sync via Make.com.

## Project Overview

This is a React + Vercel + Supabase application that tracks Magic: The Gathering tournament standings across multiple seasons. Data flows from Google Sheets → Make.com automation → Supabase → Vercel API → React frontend.

**Live:** https://colorado-pauper.org

## Tech Stack

- **Frontend**: React 19 + React Router v7 + Vite
- **Backend**: Vercel serverless functions (Node.js)
- **Database**: Supabase PostgreSQL with RLS
- **Automation**: Make.com (Google Sheets → Supabase sync)
- **Hosting**: Vercel (app + API) + custom domain (colorado-pauper.org)
- **Data Source**: Google Sheets (multi-tab structure)

## Architecture

### Data Flow

```
Google Sheets (Current Season + Archive tabs)
          ↓
    Make.com scenarios (watch for changes)
          ↓
Supabase PostgreSQL (standings, season_data, seasons tables)
          ↓
Vercel API (/api/standings.js - queries Supabase)
          ↓
React app (StandingsContext caches data)
          ↓
User sees Dashboard (current) or SeasonHistory (past)
```

### Databases Schema

#### `standings` table (current season)
- `name` (text) - player name
- `record` (text) - W-L-D format
- `points` (int4) - calculated match points
- `week` (text) - week date (M/D/YY format)
- `gwPercent` (numeric) - game win percentage
- `omwPercent` (numeric) - opposition match win percentage
- `created_at` (timestamp) - auto-created on sync

#### `season_data` table (archived seasons)
- Same columns as `standings`
- `season_name` (text) - identifies which season

#### `seasons` table
- `season_name` (text) - unique season identifier
- `is_current` (boolean) - marks active season
- `archived_at` (timestamp) - when archived

## Setup & Deployment

### Environment Variables

**Root `.env.local` (local development):**
```
VITE_SUPABASE_URL=https://rdkbhobqosqhtjaxszcd.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_KkxLEwCBrTxDgwqg4pz9Ig_LOk3Rf-R
VITE_DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
VITE_CACHE_DURATION_MS=28800000
```

**Vercel Environment Variables** (Settings → Environment Variables → Production):
```
VITE_SUPABASE_URL=https://rdkbhobqosqhtjaxszcd.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_KkxLEwCBrTxDgwqg4pz9Ig_LOk3Rf-R
```

The Vercel API reads these variables to authenticate with Supabase.

### Database Configuration

**RLS (Row Level Security)** - Enabled on all tables with public READ access:
- All three tables (`standings`, `season_data`, `seasons`) have a `public_read` policy
- Policy: SELECT only, for public role
- This allows the anon key to read but prevents unauthorized writes

### Make.com Automation

**Scenario 1: Current Season (standings → standings table)**
- Trigger: Google Sheets - Watch new rows from "Current Season" tab
- Action: Supabase - Insert row into `standings`
- Runs automatically when new data added to sheet

**Scenario 2: Archive Seasons (archive tabs → season_data table)**
- Trigger: Google Sheets - Watch new rows from archive tabs
- Action: Supabase - Insert row into `season_data`
- One scenario per archive tab (Archive - Season 1, 2, 3, etc.)

**Authentication**: Uses Supabase anon key for inserts (authorized via RLS policies)

## API Endpoints

### `/api/standings.js` (Vercel serverless function)

**Get current standings:**
```
GET /api/standings
Response: [{"name": "...", "record": "...", "points": 9, "week": "9/14/26", "gwPercent": 62.5, "omwPercent": 55.60}, ...]
```

**Get archived season data:**
```
GET /api/standings?season=Archive%20-%20Test%20Season
Response: Array of objects from season_data table
```

**Get season list:**
```
GET /api/standings?listSeasons=true
Response: ["Archive - Season 1", "Archive - Season 2", ...]
```

Uses Supabase client to query tables directly. Environment variables required.

## Frontend

### Pages

**Dashboard** (`/`) - Current season
- Weekly scores with week filter and player search (columns: Rank, Player, Points, GW%, Record, OMW%)
- Leaderboard with total points, tournaments, average, GW%, and OMW%
- Report discrepancy modal (sends to Discord webhook)
- Caches data for 8 hours
- Tiebreaker order: Points → GW% → OMW%

**Season History** (`/#/seasons`) - Past seasons
- Season dropdown selector
- Weekly scores (columns: Rank, Player, Points, GW%, Record, OMW%) and leaderboard from archived `season_data`
- Same filters and features as Dashboard
- Tiebreaker order: Points → GW% → OMW% (same as Dashboard)

### StandingsContext

Central data management context:
- `loadStandings()` - Fetches current standings, caches locally
- `loadSeasons()` - Fetches list of archived seasons
- `loadSeason(name)` - Fetches specific season data
- 8-hour localStorage cache with expiry

Data from API is object format (Supabase), not array format (Google Sheets).

### Component Notes

- `formatWeekDate()` - Converts ISO timestamps or date strings to M/D/YY format
- Type conversions: `String(dateStr)` before calling string methods to handle numeric weeks
- Pagination: 10 items per page with First/Last buttons
- Rank calculation: Done before search filter to preserve original rankings

## Development Workflow

### Local Development

```bash
cd app
npm install
npm run dev
# Open http://localhost:5173
```

Environment variables read from `.env.local`.

### Building

```bash
cd app
npm run build
# Output to ../docs (Vite configured)
npm run postbuild
# Creates CNAME and 404.html for GitHub Pages
```

### Deploying

Push to `main` branch → Vercel auto-deploys:
1. Installs dependencies (root + app)
2. Runs `npm run build --prefix app`
3. Deploys `/docs` and `/api` to Vercel

Environment variables from Vercel settings automatically available to API.

## File Structure

```
/
├── CLAUDE.md                    # This file
├── package.json                 # Root deps (@supabase/supabase-js for API)
├── vercel.json                  # Build config
├── .vercelignore                # Excludes Python files
├── .gitignore                   # node_modules, .env.local
├── api/
│   ├── standings.js             # Main API endpoint (Supabase queries)
│   └── archive-season.js        # Season archival (not currently used)
├── app/
│   ├── package.json             # Frontend deps (React, Vite, etc.)
│   ├── .env.local               # Environment variables (git ignored)
│   ├── vite.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx              # Router setup
│   │   ├── context/
│   │   │   └── StandingsContext.jsx   # Data fetching & caching
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx    # Current season
│   │   │   └── SeasonHistory.jsx # Past seasons
│   │   └── styles/
│   │       └── pages.css        # Shared table styles
│   └── docs/
│       └── index.html           # Built output
└── docs/                        # Build output (deployed by Vercel)
```

## Database Access

**Supabase project:**
- URL: https://rdkbhobqosqhtjaxszcd.supabase.co
- Anon key (public, used by app + API): `sb_publishable_KkxLEwCBrTxDgwqg4pz9Ig_LOk3Rf-R`
- Service role key: Kept secure, used only by Make.com in Vercel env

**RLS Policies:**
- All tables allow SELECT for `public` role (unauthenticated reads)
- No anonymous writes (Make.com uses service role for inserts)

## Screenshot OCR Tool

### Features

The `screenshot_to_csv.py` tool extracts Magic: The Gathering tournament standings from screenshots using OCR.

**Extracts:**
- Player names and records from tournament standings
- Win-Loss-Draw records (W-L-D format)
- Match points (auto-calculated or extracted)
- Week date
- **OMW% (Opposition Match Win %)**
- **GW% (Game Win Percentage)** - Third tiebreaker

**Note:** Colored row entries (highlighted rows without rank numbers) are skipped for reliable extraction. Focus is on cleanly extracting all ranked entries.

**Tiebreaker Order (Screenshot Tool):**
1. Match Points (higher is better)
2. OMW% (Opposition Match Win %)
3. GW% (Game Win %)

*Note: The web app (Dashboard and Season History) uses a different tiebreaker order: Points → GW% → OMW% (GW% is second tiebreaker)*

**Expected screenshot format:**
```
RANK NAME POINTS W-L-D OMW% GW%
1    Michael Ross  16    5-0-1  56.8%  62.5%
2    Matt Riecks   9     3-0-0  44.4%  50.0%
```

**Setup:**
```bash
# Install dependencies
pip install -r requirements.txt
```

**Usage:**
```bash
# Extract from single screenshot
python screenshot_to_csv.py standings.png -o standings.xlsx

# Specify week date
python screenshot_to_csv.py standings.png -d 9/23/26 -o week.xlsx

# Merge multiple screenshots (combines data from multiple rounds)
python screenshot_to_csv.py round1.png round2.png -o merged.xlsx

# Debug mode (shows OCR parsing details)
python screenshot_to_csv.py standings.png --debug
```

**Output:**
- Excel file with columns: Name, Record, Week, Points, OMW%, GW%
- Filename includes date: `standings_M_D_YY.xlsx`
- Sorted by Points (highest first), then OMW%, then GW%
- Only includes ranked entries (colored rows are skipped for data quality)

## Common Tasks

### Add a new season
1. Create "Archive - [Season Name]" tab in Google Sheets
2. Create new Make scenario: Watch sheet → Insert to `season_data` table
3. Add season to `seasons` table (via Supabase console or API)
4. Data syncs automatically

### Update current standings
1. Add/edit rows in "Current Season" tab in Google Sheets
2. Make automatically detects change within 1-2 minutes
3. Row inserted to `standings` table
4. App cache expires in 8 hours (or user can clear localStorage)

### Clear app cache
DevTools → Application → Local Storage → Delete `mtg_cache_*` entries

### Deploy changes
```bash
git add .
git commit -m "description"
git push origin main
# Vercel auto-deploys in ~2 minutes
```

## Troubleshooting

**504 Gateway Timeout:**
- Check Vercel env vars are set (Settings → Environment Variables)
- Ensure RLS policies allow public READ on all tables
- Check Supabase tables have data

**"No data available":**
- Clear localStorage cache (DevTools → Application → Local Storage)
- Verify season exists in `seasons` table
- Check Make scenario actually synced data to Supabase

**OMW% column missing:**
- Verify `omwPercent` column exists in Supabase table
- Check column name matches exactly (case-sensitive)

**API still calling Google Apps Script:**
- Verify `api/standings.js` has Supabase code (imports `@supabase/supabase-js`)
- Confirm root `package.json` has `@supabase/supabase-js` in dependencies
- Redeploy on Vercel after code changes

## Performance & Caching

- **Frontend cache**: 8-hour localStorage TTL
- **API queries**: Direct to Supabase (no caching layer)
- **Data sync**: ~1-2 minute latency from Google Sheets → Make → Supabase
- **Vercel function timeout**: 10-60s (depends on plan)

## Security Notes

- `.env.local` contains secrets → git ignored
- Supabase anon key is public (used in browser)
- RLS policies restrict access (reads only, writes blocked)
- Discord webhook URL is public (but read-only)
- Service role key stored in Vercel (not in git)

## Future Improvements

- [ ] Migrate screenshot OCR tool to web interface
- [ ] Live leaderboard updates (WebSocket instead of polling)
- [ ] Season archival automation (currently manual)
- [ ] Custom styling/branding options
- [ ] Mobile-responsive improvements
