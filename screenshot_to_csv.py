#!/usr/bin/env python3
"""
Magic: The Gathering Tournament Standings Screenshot to CSV Converter

Converts Magic: The Gathering tournament standings screenshots to CSV format
with automatic match point calculation. Supports Win/Loss/Draw records and round tracking.
Handles colored rows using PaddleOCR with Tesseract fallback.
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

# Try to import PaddleOCR for better colored text handling
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

# Try to import numpy for image preprocessing
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

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


def preprocess_image_for_ocr(image: Image) -> Image:
    """
    Preprocess image to handle colored rows better.
    Neutralizes saturated colors (like colored backgrounds) to improve OCR.
    """
    if not NUMPY_AVAILABLE:
        return image

    try:
        img_array = np.array(image)

        # Convert to RGB if needed
        if len(img_array.shape) == 2:  # Grayscale
            return image

        if img_array.shape[2] == 4:  # RGBA
            img_array = img_array[:, :, :3]

        # Detect saturated pixels (colored backgrounds)
        # High saturation indicates strong color
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        max_val = np.maximum(np.maximum(r, g), b)
        min_val = np.minimum(np.minimum(r, g), b)

        # Saturation = (max - min) / max, where max > 0
        saturation = np.zeros_like(max_val, dtype=float)
        mask = max_val > 0
        saturation[mask] = (max_val[mask] - min_val[mask]) / max_val[mask]

        # Neutralize highly saturated pixels (> 0.25 saturation = colored)
        colored_mask = saturation > 0.25

        # Convert colored pixels to grayscale
        if np.any(colored_mask):
            gray_val = (img_array[:,:,0].astype(float) * 0.299 +
                       img_array[:,:,1].astype(float) * 0.587 +
                       img_array[:,:,2].astype(float) * 0.114).astype(np.uint8)
            img_array[colored_mask] = gray_val[colored_mask, np.newaxis]

        # Enhance contrast and sharpness
        enhanced = Image.fromarray(img_array)
        from PIL import ImageEnhance
        enhanced = ImageEnhance.Contrast(enhanced).enhance(1.5)
        enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)

        return enhanced
    except Exception as e:
        print(f"Warning: Preprocessing failed, using original image: {e}")
        return image


def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using PaddleOCR (primary) or Tesseract (fallback)."""
    try:
        image = Image.open(image_path)

        # Preprocess for colored rows
        image = preprocess_image_for_ocr(image)

        # Try PaddleOCR first if available (better for colored text)
        if PADDLEOCR_AVAILABLE:
            try:
                print("Using PaddleOCR for text extraction...")
                ocr = PaddleOCR(use_angle_cls=True, lang='en')
                result = ocr.ocr(image_path, cls=True)

                # Convert PaddleOCR output to text
                text_lines = []
                if result:
                    for line in result:
                        if line:
                            for word_info in line:
                                text_lines.append(word_info[1][0])  # Extract text

                text = '\n'.join(text_lines)
                if text.strip():
                    return text
            except Exception as e:
                print(f"PaddleOCR failed, falling back to Tesseract: {e}")

        # Fallback to Tesseract
        print("Using Tesseract for text extraction...")
        text = pytesseract.image_to_string(image)
        return text

    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""


def parse_standings(text: str) -> List[Dict[str, any]]:
    """
    Parse Magic: The Gathering tournament standings text from OCR.
    Handles colored rows that may fragment the output.

    Expected format (from the screenshot):
    RANK NAME POINTS W-L-D OMW% GW%
    1    Michael Ross  16    5-0-1  56.8%  62.5%
    """
    lines = text.strip().split('\n')

    # Phase 1: Group fragmented lines by rank markers (1-50)
    # Colored rows cause OCR to split a single entry across multiple lines
    merged_lines = []
    current_group = []

    rank_pattern = r'^([1-9]|[1-4]\d|50)\s+'

    for line in lines:
        line = line.strip()
        if not line or line.upper().startswith('RANK') or line.upper().startswith('MATCH'):
            continue

        # Check if this line starts with a rank marker
        if re.match(rank_pattern, line):
            # New rank marker found - save previous group if it exists
            if current_group:
                merged_lines.append(' '.join(current_group))
            current_group = [line]
        else:
            # Continuation of previous entry (orphaned data)
            current_group.append(line)

    # Don't forget the last group
    if current_group:
        merged_lines.append(' '.join(current_group))

    # Phase 2: Parse merged lines
    standings = []
    orphaned_records = []
    orphaned_names = []
    orphaned_points = []

    for merged_line in merged_lines:
        parts = merged_line.split()

        if len(parts) < 3:
            continue

        try:
            rank = None
            idx = 0

            if parts[0].isdigit():
                rank = int(parts[0])
                idx = 1

            record_pattern = r'\d{1,2}-\d{1,2}(?:-\d{1,2})?'

            # Find all records in this line (there might be orphaned ones)
            record_matches = []
            for i, part in enumerate(parts[idx:], start=idx):
                if re.search(record_pattern, part):
                    record_matches.append((i, part))

            if not record_matches:
                continue

            # Use first record for this entry
            record_idx, record = record_matches[0]

            # Extract points (should be right before the record)
            points = None
            points_idx = record_idx - 1

            if points_idx >= idx:
                points_str = parts[points_idx]
                if points_str.isdigit():
                    points = int(points_str)
                    name_parts = parts[idx:points_idx]
                else:
                    name_parts = parts[idx:record_idx]
            else:
                name_parts = parts[idx:record_idx]

            name = ' '.join(name_parts)
            name = clean_name(name)

            if points is None:
                points = calculate_points(record)

            # Extract OMW% and GW% (percentages after record)
            omw = None
            gw = None
            pct_idx = record_idx + 1

            if pct_idx < len(parts):
                potential_omw = parts[pct_idx]
                omw_match = re.search(r'(\d+(?:\.\d+)?)\s*%', potential_omw)
                if omw_match:
                    omw = float(omw_match.group(1))
                    pct_idx += 1

            if pct_idx < len(parts):
                potential_gw = parts[pct_idx]
                gw_match = re.search(r'(\d+(?:\.\d+)?)\s*%', potential_gw)
                if gw_match:
                    gw = float(gw_match.group(1))

            if name and record:
                standings.append({
                    'name': name.strip(),
                    'record': record,
                    'points': points,
                    'omw': omw,
                    'gw': gw
                })

            # Collect orphaned records (additional records in same line)
            if len(record_matches) > 1:
                for orphan_idx, orphan_record in record_matches[1:]:
                    orphaned_records.append(orphan_record)

            # Collect orphaned names that don't have points before them
            for i in range(idx, len(parts)):
                part = parts[i]
                # If it's a name (not a number or record or percentage)
                if (not part.isdigit() and
                    not re.search(record_pattern, part) and
                    not re.search(r'%', part) and
                    i not in [idx + j for j in range(len(name_parts))]):
                    if len(clean_name(part)) > 2:  # Reasonable name length
                        orphaned_names.append(part)

            # Collect orphaned points (numbers not followed by records)
            for i, part in enumerate(parts[idx:], start=idx):
                if part.isdigit() and i + 1 < len(parts):
                    next_part = parts[i + 1]
                    if (not re.search(record_pattern, next_part) and
                        not re.search(r'%', next_part)):
                        orphaned_points.append(int(part))

        except Exception as e:
            continue

    # Phase 3: Try to match orphaned data
    for orphan_record in orphaned_records:
        # Try to find matching name and points
        matched = False
        if orphaned_names:
            name = clean_name(orphaned_names.pop(0))
            points = orphaned_points.pop(0) if orphaned_points else calculate_points(orphan_record)

            standings.append({
                'name': name.strip(),
                'record': orphan_record,
                'points': points,
                'omw': None,
                'gw': None
            })
            matched = True

        if not matched:
            # At least save the record with a placeholder name
            standings.append({
                'name': '[Colored Row - Name Lost]',
                'record': orphan_record,
                'points': calculate_points(orphan_record),
                'omw': None,
                'gw': None
            })

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


def write_csv(standings: List[Dict[str, any]], output_path: str, include_omw: bool = True, include_gw: bool = True):
    """Write standings to CSV file."""
    if not standings:
        print("No data to write")
        return

    # Define CSV columns
    fieldnames = ['name', 'record', 'week', 'points']
    if include_omw:
        fieldnames.append('omw')
    if include_gw:
        fieldnames.append('gw')

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


def write_excel(standings: List[Dict[str, any]], output_path: str, include_omw: bool = True, include_gw: bool = True):
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
            headers.append('OMW')
        if include_gw:
            headers.append('GW')

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
            if include_gw:
                col_idx = 6 if include_omw else 5
                ws.cell(row=row_idx, column=col_idx).value = entry.get('gw', '')

        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 10
        if include_omw:
            ws.column_dimensions['E'].width = 10
        if include_gw:
            col_idx = 'F' if include_omw else 'E'
            ws.column_dimensions[col_idx].width = 10

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
  python screenshot_to_csv.py screenshot.png -o standings.xlsx
  python screenshot_to_csv.py screenshot.png -d 9/14/26 -o week.xlsx -s "Store Name"
  python screenshot_to_csv.py img1.png img2.png -o merged.xlsx --json standings.json

If no output path specified, uses: standings_M_D_YY.xlsx (where date is from -d or today)
        '''
    )

    parser.add_argument(
        'images',
        nargs='+',
        help='Screenshot image file(s) to process'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output Excel file path (default: standings_M_D_YY.xlsx with date included)'
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
        '--no-gw',
        action='store_true',
        help='Exclude GW%% column from output (default: included)'
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

    # Add store name if provided
    if args.store:
        for entry in all_standings:
            entry['store'] = args.store

    # Filter out opted-out players
    all_standings = filter_opt_out_players(all_standings)

    # Determine output filename if not specified
    output_path = args.output
    if not output_path:
        # Extract date from standings or use provided date or current
        week_date = args.date if args.date else get_week_start_date()
        # Convert M/D/YY to filename format (M_D_YY)
        week_date_formatted = week_date.replace('/', '_')
        output_path = f'standings_{week_date_formatted}.xlsx'

    # Write Excel (main output format)
    include_omw = not args.no_omw
    include_gw = not args.no_gw
    write_excel(all_standings, output_path, include_omw=include_omw, include_gw=include_gw)

    # Write JSON if requested
    if args.json:
        write_json(all_standings, args.json)


if __name__ == '__main__':
    main()
