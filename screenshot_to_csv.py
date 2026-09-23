#!/usr/bin/env python3
"""
Magic: The Gathering Tournament Standings Screenshot to CSV Converter

Converts Magic: The Gathering tournament standings screenshots to CSV format
with automatic match point calculation. Supports Win/Loss/Draw records and round tracking.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Player opt-out list - players who don't want their data represented
# Can be overridden by OPT_OUT_PLAYERS environment variable
OPT_OUT_PLAYERS: List[str] = []


def clean_name(name: str) -> str:
    """
    Clean player name by removing emojis and non-alphabetic characters.
    Keeps spaces and hyphens/apostrophes common in names.
    """
    # Remove emojis and non-ASCII characters
    cleaned = name.encode('ascii', 'ignore').decode('ascii')
    # Keep only letters, spaces, hyphens, and apostrophes
    cleaned = re.sub(r"[^a-zA-Z\s\-']", '', cleaned)
    # Collapse multiple spaces into one
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def calculate_points(record: str) -> int:
    """
    Calculate points from a W-L-D record.

    Win = 3 points, Loss = 0 points, Draw = 1 point
    Example: "4-2-0" = 4*3 + 2*0 + 0*1 = 12 points
    """
    # Extract W-L-D numbers from various formats
    pattern = r'(\d{1,2})-(\d{1,2})(?:-(\d{1,2}))?'
    match = re.search(pattern, record)

    if not match:
        return 0

    wins = int(match.group(1))
    losses = int(match.group(2))
    draws = int(match.group(3)) if match.group(3) else 0

    points = (wins * 3) + (losses * 0) + (draws * 1)
    return points


def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using OCR."""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""


def parse_standings(text: str, debug: bool = False) -> List[Dict[str, any]]:
    """
    Parse Magic: The Gathering tournament standings text from OCR.

    Expected format (from the screenshot):
    RANK NAME POINTS W-L-D OMW% GW%
    1    Michael Ross  16    5-0-1  56.8%  62.5%

    Tiebreakers (in order): Points → OMW% → GW%
    """
    lines = text.strip().split('\n')
    standings = []

    for line in lines:
        line = line.strip()
        if not line or line.upper().startswith('RANK') or line.upper().startswith('MATCH'):
            continue

        parts = line.split()

        if len(parts) < 3:
            continue

        try:
            rank = None
            idx = 0

            if parts[0].isdigit():
                rank = int(parts[0])
                idx = 1

            record_pattern = r'\d{1,2}-\d{1,2}(?:-\d{1,2})?'
            record = None
            record_idx = None

            for i in range(idx, len(parts)):
                if re.search(record_pattern, parts[i]):
                    record = parts[i]
                    record_idx = i
                    break

            if not record:
                continue

            # Extract points (should be right before the record)
            points = None
            points_idx = record_idx - 1

            if points_idx >= idx:
                points_str = parts[points_idx]
                if points_str.isdigit():
                    points = int(points_str)
                    # Name is everything between rank and points
                    name_parts = parts[idx:points_idx]
                else:
                    # No explicit points, name includes what we thought was points
                    name_parts = parts[idx:record_idx]
            else:
                name_parts = parts[idx:record_idx]

            name = ' '.join(name_parts)
            # Clean the name to remove emojis and non-alphabetic characters
            name = clean_name(name)

            # If no explicit points found, calculate from record
            if points is None:
                points = calculate_points(record)

            # Extract OMW% and GW% if present
            # Look for all percentages after the record
            omw = None
            gw = None
            percentages = []

            # Collect all percentage values after the record position
            for i in range(record_idx + 1, len(parts)):
                percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', parts[i])
                if percent_match:
                    # Ensure value is between 0 and 100
                    value = float(percent_match.group(1))
                    if 0 <= value <= 100:
                        percentages.append(value)

            # Assign first two percentages found to OMW% and GW%
            if len(percentages) >= 1:
                omw = percentages[0]
            if len(percentages) >= 2:
                gw = percentages[1]

            if name and record:
                standings.append({
                    'name': name.strip(),
                    'record': record,
                    'points': points,
                    'omw': omw,
                    'gw': gw
                })

        except Exception as e:
            # Skip lines that don't parse
            if debug:
                print(f"Debug: Skipped line: {line}")
                print(f"  Error: {e}")
            continue

    return standings


def process_screenshot(image_path: str, week_start: Optional[str] = None, debug: bool = False) -> List[Dict[str, any]]:
    """
    Process a single screenshot and return standings data.
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return []

    print(f"Processing: {image_path}")
    text = extract_text_from_image(image_path)
    standings = parse_standings(text, debug=debug)

    if week_start is None:
        week_start = get_week_start_date()

    for entry in standings:
        entry['week'] = week_start

    return standings


def get_week_start_date() -> str:
    """
    Get the Monday of the current week in M/D/YY format.
    """
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    month = monday.month
    day = monday.day
    year = monday.strftime('%y')
    return f"{month}/{day}/{year}"


def parse_date_string(date_str: str) -> datetime:
    """
    Parse a date string in M/D/YY or M/D/YYYY format.
    """
    try:
        return datetime.strptime(date_str, '%m/%d/%y')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use M/D/YY or M/D/YYYY")


def load_opt_out_list() -> List[str]:
    """
    Load the list of players who have opted out of data tracking.
    Players can be specified two ways:
    1. OPT_OUT_PLAYERS environment variable (comma-separated list)
    2. OPT_OUT_PLAYERS global variable (list of strings)

    Environment variable takes precedence if set.
    Example: OPT_OUT_PLAYERS="John Doe,Jane Smith"
    """
    global OPT_OUT_PLAYERS

    # Check environment variable first
    opt_out_env = os.getenv('OPT_OUT_PLAYERS', '')
    if opt_out_env.strip():
        # Split by comma and clean up each name
        return [name.strip().lower() for name in opt_out_env.split(',') if name.strip()]

    # Fall back to global variable (convert to lowercase for comparison)
    return [name.lower() for name in OPT_OUT_PLAYERS]


def filter_opt_out_players(standings: List[Dict[str, any]]) -> List[Dict[str, any]]:
    """
    Filter out players who have opted out of data tracking.
    """
    opt_out_list = load_opt_out_list()
    if not opt_out_list:
        return standings

    filtered = [entry for entry in standings if entry['name'].lower() not in opt_out_list]
    removed_count = len(standings) - len(filtered)
    if removed_count > 0:
        print(f"Filtered out {removed_count} opted-out player(s)")
    return filtered


def merge_standings(*files_list) -> List[Dict[str, any]]:
    """
    Merge standings from multiple sources, combining data from the same player.
    When a player appears in multiple screenshots:
    - Uses the highest points value
    - Fills in missing percentages from other entries
    - Prioritizes non-None values
    """
    seen_names = {}

    for file_data in files_list:
        if isinstance(file_data, list):
            for entry in file_data:
                name = entry['name'].lower()

                if name not in seen_names:
                    # First time seeing this player
                    seen_names[name] = entry.copy()
                else:
                    # Player already exists - merge the data
                    existing = seen_names[name]

                    # Keep higher points
                    if entry['points'] > existing['points']:
                        existing['points'] = entry['points']
                        existing['record'] = entry['record']

                    # Fill in missing OMW% if this entry has it
                    if entry.get('omw') is not None and existing.get('omw') is None:
                        existing['omw'] = entry['omw']

                    # Fill in missing GW% if this entry has it
                    if entry.get('gw') is not None and existing.get('gw') is None:
                        existing['gw'] = entry['gw']

    return list(seen_names.values())


def write_csv(standings: List[Dict[str, any]], output_path: str, include_omw: bool = True):
    """Write standings to CSV file."""
    if not standings:
        print("No data to write")
        return

    # Define CSV columns
    fieldnames = ['name', 'record', 'week', 'points']
    if include_omw:
        fieldnames.extend(['omw', 'gw'])

    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()

            for entry in standings:
                row = {field: entry.get(field) for field in fieldnames}
                writer.writerow(row)

        print(f"CSV written to: {output_path}")
        print(f"Total entries: {len(standings)}")
    except Exception as e:
        print(f"Error writing CSV: {e}")


def write_json(standings: List[Dict[str, any]], output_path: str):
    """Write standings to JSON file."""
    if not standings:
        print("No data to write")
        return

    try:
        import json
        with open(output_path, 'w') as jsonfile:
            json.dump(standings, jsonfile, indent=2)

        print(f"JSON written to: {output_path}")
    except Exception as e:
        print(f"Error writing JSON: {e}")


def write_excel(standings: List[Dict[str, any]], output_path: str, include_omw: bool = True):
    """Write standings to Excel file."""
    if not standings:
        print("No data to write")
        return

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = "Standings"

        # Define headers
        headers = ['Name', 'Record', 'Week', 'Points']
        if include_omw:
            headers.extend(['OMW%', 'GW%'])

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Write data
        for row_idx, entry in enumerate(standings, 2):
            ws.cell(row=row_idx, column=1).value = entry.get('name', '')
            ws.cell(row=row_idx, column=2).value = entry.get('record', '')
            ws.cell(row=row_idx, column=3).value = entry.get('week', '')
            ws.cell(row=row_idx, column=4).value = entry.get('points', 0)
            if include_omw:
                ws.cell(row=row_idx, column=5).value = entry.get('omw', '')
                ws.cell(row=row_idx, column=6).value = entry.get('gw', '')

        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 10
        if include_omw:
            ws.column_dimensions['E'].width = 10
            ws.column_dimensions['F'].width = 10

        wb.save(output_path)
        print(f"Excel written to: {output_path}")
        print(f"Total entries: {len(standings)}")
    except Exception as e:
        print(f"Error writing Excel: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Magic: The Gathering tournament standings screenshots to Excel/JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python screenshot_to_csv.py screenshot.png
  python screenshot_to_csv.py screenshot.png -d 9/14/26 -s "Store Name"
  python screenshot_to_csv.py img1.png img2.png --json standings.json
  python screenshot_to_csv.py screenshot.png -o custom_name.xlsx
  # Merge multiple screenshots (e.g., one with OMW%, another with GW%)
  python screenshot_to_csv.py standings_omw.png standings_gw.png
        '''
    )

    parser.add_argument(
        'images',
        nargs='+',
        help='Screenshot image file(s) to process'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output Excel file path (default: standings_[date].xlsx)'
    )

    parser.add_argument(
        '-d', '--date',
        help='Week start date in M/D/YY format (default: current week Monday)'
    )

    parser.add_argument(
        '-s', '--store',
        help='Store/event name for tracking (optional)'
    )

    parser.add_argument(
        '--json',
        help='Output JSON file path (optional, for artifact database)'
    )

    parser.add_argument(
        '--no-omw',
        action='store_true',
        help='Exclude OMW%% column from output (default: included)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output to see OCR parsing details'
    )

    args = parser.parse_args()

    # Determine week start date (needed for default filename)
    week_start = args.date if args.date else get_week_start_date()

    # Generate default output filename with date if not provided
    if not args.output:
        # Format date for filename (replace slashes with underscores)
        date_str = week_start.replace('/', '_')
        args.output = f'standings_{date_str}.xlsx'

    all_standings = []

    # Process each image
    for image_path in args.images:
        standings = process_screenshot(image_path, week_start=week_start, debug=args.debug)
        all_standings.extend(standings)

    # Merge and remove duplicates
    if len(args.images) > 1:
        all_standings = merge_standings(all_standings)

    # Add store name if provided
    if args.store:
        for entry in all_standings:
            entry['store'] = args.store

    # Filter out opted-out players
    all_standings = filter_opt_out_players(all_standings)

    # Write Excel (main output format)
    include_omw = not args.no_omw
    write_excel(all_standings, args.output, include_omw=include_omw)

    # Write JSON if requested
    if args.json:
        write_json(all_standings, args.json)


if __name__ == '__main__':
    main()
