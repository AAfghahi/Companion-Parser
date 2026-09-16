#!/usr/bin/env python3
"""
Magic: The Gathering Tournament Standings Screenshot to CSV Converter

Converts Magic: The Gathering tournament standings screenshots to CSV format
with automatic match point calculation. Supports Win/Loss/Draw records and round tracking.
"""

import argparse
import csv
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
    pattern = r'(\d+)-(\d+)(?:-(\d+))?'
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


def parse_standings(text: str) -> List[Dict[str, any]]:
    """
    Parse Magic: The Gathering tournament standings text from OCR.

    Expected format (from the screenshot):
    RANK NAME POINTS W-L-D OMW%
    1    Michael Ross  16    5-0-1  56.8%
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

            record_pattern = r'\d+-\d+(?:-\d+)?'
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

            if name and record:
                standings.append({
                    'name': name.strip(),
                    'record': record,
                    'points': points,
                    'omw': None  # Optional: could parse OMW% if needed
                })

        except Exception as e:
            # Skip lines that don't parse
            continue

    return standings


def process_screenshot(image_path: str, week_start: Optional[str] = None) -> List[Dict[str, any]]:
    """
    Process a single screenshot and return standings data.
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return []

    print(f"Processing: {image_path}")
    text = extract_text_from_image(image_path)
    standings = parse_standings(text)

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


def merge_standings(*files_list) -> List[Dict[str, any]]:
    """
    Merge standings from multiple sources, removing duplicates by name.
    Entry with the best record (highest points) is kept.
    """
    seen_names = {}

    for file_data in files_list:
        if isinstance(file_data, list):
            for entry in file_data:
                name = entry['name'].lower()
                # Keep the entry with the higher points
                if name not in seen_names or entry['points'] > seen_names[name]['points']:
                    seen_names[name] = entry

    return list(seen_names.values())


def write_csv(standings: List[Dict[str, any]], output_path: str, include_omw: bool = False):
    """Write standings to CSV file."""
    if not standings:
        print("No data to write")
        return

    # Define CSV columns
    fieldnames = ['name', 'record', 'week', 'points']
    if include_omw:
        fieldnames.append('omw')

    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for entry in standings:
                row = {field: entry.get(field) for field in fieldnames}
                writer.writerow(row)

        print(f"CSV written to: {output_path}")
        print(f"Total entries: {len(standings)}")
    except Exception as e:
        print(f"Error writing CSV: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Convert Magic: The Gathering tournament standings screenshots to CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python screenshot_to_csv.py screenshot.png -o standings.csv
  python screenshot_to_csv.py screenshot.png -d 9/14/26 -o week.csv
  python screenshot_to_csv.py img1.png img2.png -o merged.csv
        '''
    )

    parser.add_argument(
        'images',
        nargs='+',
        help='Screenshot image file(s) to process'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output CSV file path (default: standings.csv)',
        default='standings.csv'
    )

    parser.add_argument(
        '-d', '--date',
        help='Week start date in M/D/YY format (default: current week Monday)'
    )

    parser.add_argument(
        '--omw',
        action='store_true',
        help='Include OMW% column in output'
    )

    args = parser.parse_args()

    all_standings = []

    # Process each image
    for image_path in args.images:
        standings = process_screenshot(image_path, week_start=args.date)
        all_standings.extend(standings)

    # Merge and remove duplicates
    if len(args.images) > 1:
        all_standings = merge_standings(all_standings)

    # Write CSV
    write_csv(all_standings, args.output, include_omw=args.omw)


if __name__ == '__main__':
    main()
