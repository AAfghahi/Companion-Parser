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
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re

try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


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


def process_screenshot(image_path: str, week: Optional[int] = None) -> List[Dict[str, any]]:
    """
    Process a single screenshot and return standings data.
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return []

    print(f"Processing: {image_path}")
    text = extract_text_from_image(image_path)
    standings = parse_standings(text)

    # Add week information
    if week is None:
        week = get_current_week()

    for entry in standings:
        entry['week'] = week

    return standings


def get_current_week() -> int:
    """
    Get the current week number (1-52/53 based on ISO week).
    """
    return datetime.now().isocalendar()[1]


def merge_standings(*files_list) -> List[Dict[str, any]]:
    """
    Merge standings from multiple sources, removing duplicates by name.
    Latest entry for each name is kept.
    """
    seen_names = {}

    for file_data in files_list:
        if isinstance(file_data, list):
            for entry in file_data:
                name = entry['name'].lower()
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
        description='Convert sports standings screenshots to CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python screenshot_to_csv.py screenshot.png -o standings.csv
  python screenshot_to_csv.py screenshot.png -w 5 -o week5.csv
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
        '-w', '--week',
        type=int,
        help='Week number (default: current week)'
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
        standings = process_screenshot(image_path, week=args.week)
        all_standings.extend(standings)

    # Merge and remove duplicates
    if len(args.images) > 1:
        all_standings = merge_standings(all_standings)

    # Write CSV
    write_csv(all_standings, args.output, include_omw=args.omw)


if __name__ == '__main__':
    main()
