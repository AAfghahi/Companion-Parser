#!/usr/bin/env python3
"""
Magic: The Gathering Tournament Standings Extractor v3

Robust parser handling scrambled table OCR layouts where columns are interleaved.
- Supports multiple screenshots with deduplication and data merging
- Table format: Can handle OCR text with rows/columns in mixed order
- Column format: Separate NAME, POINTS, OMW% sections
"""

import argparse
import os
import sys
from pathlib import Path
import re
import csv
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from difflib import get_close_matches

# Known players list for Colorado Pauper tournament
KNOWN_PLAYERS = [
    'Neil Brady',
    'Callie Linn',
    'Matt Riecks',
    'Tommy Adams',
    'Willow Parker',
    'Ve Marie',
    'Julien Hamann',
    'Alexander Stautheim',
    'Michael Ross',
    'Michael Dong',
    'Tim Mulcahy',
    'Lynn Adams',
    'Bryce Kari',
    'Ct Donohue',
    'Clayton Watkins',
    'Rick Willison',
    'Conifer OSulli',
    'Alex Brown',
    'Sergio Sandoval',
    'Dustin Gault',
    'Gina Griffin',
    'Hayden Sapp',
    'Nick Orichella',
    'Ramona Hageman',
    'Steve Rubenkoenig',
    'Chris Kennedy',
    'Nathan Shiflet',
    'Nick Caroselli',
    'arash afghahi',
]

try:
    from PIL import Image, ImageEnhance
    import pytesseract
except ImportError:
    print("Error: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
except ImportError:
    print("Error: openpyxl not installed. Run: pip install openpyxl")
    sys.exit(1)


def preprocess_image(image: Image.Image) -> Image.Image:
    """Apply contrast/sharpness enhancement."""
    # Convert to grayscale for more consistent OCR across platforms
    if image.mode != 'L':
        image = image.convert('L')

    # Apply moderate contrast enhancement (reduced from 1.5 to 1.2)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)

    # Apply moderate sharpness enhancement (reduced from 2.0 to 1.5)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)

    return image


def extract_ocr_text(image_path: str) -> str:
    """Extract text from image using Tesseract."""
    image = Image.open(image_path)
    image = preprocess_image(image)
    text = pytesseract.image_to_string(image)
    return text


def clean_name(name: str) -> str:
    """Clean player name: remove special chars, keep letters/spaces."""
    name = name.replace('tS)', '').replace(')', '')
    cleaned = name.encode('ascii', 'ignore').decode('ascii')
    cleaned = re.sub(r"[^a-zA-Z\s\-']", '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def recover_unknowns(standings: List[Dict], all_extracted_names: List[str]) -> List[Dict]:
    """Recover Unknown entries and truncated names by fuzzy matching against known players."""
    known_players_lower = {p.lower(): p for p in KNOWN_PLAYERS}
    used_names = set()

    for entry in standings:
        name = entry['name']
        name_lower = name.lower()

        # Skip if already a known player (exact match)
        if name_lower in known_players_lower:
            used_names.add(name_lower)
            entry['name'] = known_players_lower[name_lower]
            continue

        # Get available players (not yet assigned)
        available_players = [p for p in KNOWN_PLAYERS if p.lower() not in used_names]
        if not available_players:
            continue

        # Determine cutoff: more lenient for Unknown entries, stricter for partial names
        if name.startswith('Unknown_'):
            cutoff = 0.4
        else:
            cutoff = 0.6

        matches = get_close_matches(name, available_players, n=1, cutoff=cutoff)
        if matches:
            best_match = matches[0]
            entry['name'] = best_match
            used_names.add(best_match.lower())

    return standings


def calculate_points(record: str) -> int:
    """Calculate points: Win=3, Loss=0, Draw=1."""
    match = re.search(r'(\d+)-(\d+)(?:-(\d+))?', record)
    if not match:
        return 0
    wins = int(match.group(1))
    losses = int(match.group(2))
    draws = int(match.group(3)) if match.group(3) else 0
    return wins * 3 + draws * 1


def get_week_start_date() -> str:
    """Get the Monday of the current week in M/D/YY format."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    month = monday.month
    day = monday.day
    year = monday.strftime('%y')
    return f"{month}/{day}/{year}"


def parse_date_string(date_str: str) -> datetime:
    """Parse a date string in M/D/YY or M/D/YYYY format."""
    try:
        return datetime.strptime(date_str, '%m/%d/%y')
    except ValueError:
        try:
            return datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use M/D/YY or M/D/YYYY")


def parse_standings_table_format(lines: List[str], record_pattern: str) -> Optional[List[Dict]]:
    """Parse table format with complete rows, and recover orphaned names/records from colored rows."""

    header_idx = -1
    for i, line in enumerate(lines):
        if 'RANK' in line.upper() and 'NAME' in line.upper():
            header_idx = i
            break

    if header_idx == -1:
        return None

    standings = []
    orphaned_records = []  # Records without associated names (from colored rows)
    orphaned_names = []    # Names without associated records (from colored rows) - just the names
    standalone_names = []  # Names with no rank or record (separate line)
    last_complete_rank = 0

    for line in lines[header_idx + 1:]:
        line_upper = line.upper()

        # Skip metadata lines
        if any(kw in line_upper for kw in ['STANDINGS', 'MATCH', 'ROUND', 'ASOF']):
            continue
        if line.startswith(('«', '>', '<', '◆', '♦', '●', '◉', '»', '~', ')')):
            continue
        if not line or len(line.strip()) < 1:
            continue

        # Extract rank (should be first number), or convert misread OCR characters to digits
        # Handle common OCR misreads like O (10), I (1), etc.
        line_fixed = line
        if len(line) > 1 and line[0] in 'OoIlZ':
            # Check for two-digit rank misreads like "IO" (should be "10")
            if line[0] in 'OoIl' and line[1].isdigit():
                # "O#" or "I#" -> "1#" (rank 10-19, e.g., "O3" -> "13")
                line_fixed = '1' + line[1:]
            elif line[0] == 'O' and line[1] == ' ':
                # "O " (standalone) -> likely "10 " where first digit got misread
                line_fixed = '10 ' + line[2:].lstrip()
            elif line[0] in 'OoIl' and line[1] == ' ':
                # "I " or "l " -> "1 " (single digit misread)
                line_fixed = '1 ' + line[2:].lstrip()
            else:
                # Other single digit misreads
                ocr_to_digit = {'O': '0', 'o': '0', 'I': '1', 'l': '1', 'Z': '2'}
                if line[0] in ocr_to_digit:
                    line_fixed = ocr_to_digit[line[0]] + line[1:]

        rank_match = re.match(r'^(\d{1,2})[.\s]+', line_fixed)
        if not rank_match:
            # No rank at start: might be orphaned record, orphaned name, or standalone rank/name
            records = re.findall(record_pattern, line)
            if records:
                # Orphaned record line (has record but no rank/name)
                orphaned_records.append((records[0], line))
                continue

            # Check if line is just a rank number (e.g., "6" or "7")
            if re.match(r'^\d{1,2}$', line.strip()):
                standalone_ranks.append(int(line.strip()))
                continue

            # Check if line is a name (has letters but no digits/records)
            if any(c.isalpha() for c in line) and not re.search(r'\d{1,2}-\d{1,2}', line):
                name = clean_name(line)
                if name and len(name) > 1:
                    standalone_names.append(name)
                continue

            continue

        rank = int(rank_match.group(1))

        # Skip rank 0 or very high ranks (likely garbage/misread)
        if rank == 0 or rank > 50:
            continue

        last_complete_rank = rank

        # Remove rank from fixed line for further processing
        line_without_rank = re.sub(r'^\d{1,2}[.\s]+', '', line_fixed).strip()

        # Extract all records from the line
        records = re.findall(record_pattern, line)
        if not records:
            # No record: might be orphaned name (ignore rank, just collect name)
            orphaned_names.append(line_without_rank)
            continue

        record = records[0]

        # Extract all percentages from the line
        percents = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)

        # Extract name: remove record and percentages, clean up
        name_candidate = line_without_rank
        # Remove all records
        for rec in records:
            name_candidate = name_candidate.replace(rec, '').strip()
        # Remove all percentages
        for perc in percents:
            name_candidate = name_candidate.replace(f"{perc}%", '').replace(perc, '').strip()
        # Remove points (number before record)
        name_candidate = re.sub(r'\s*\d+\s*(?=' + record_pattern + ')', '', name_candidate).strip()

        if name_candidate and len(name_candidate) > 1:
            name = clean_name(name_candidate)
            if name and len(name) > 1:
                points = calculate_points(record)
                omw = float(percents[0]) if len(percents) > 0 else None
                gw = float(percents[1]) if len(percents) > 1 else None

                standings.append({
                    'rank': rank,
                    'name': name,
                    'record': record,
                    'points': points,
                    'omw': omw,
                    'gw': gw
                })

    # Combine all names (standalone + orphaned) and match with records by position
    all_names = standalone_names + orphaned_names

    # Clean all names
    cleaned_names = []
    for name_text in all_names:
        name = clean_name(name_text)
        if name and len(name) > 1:
            cleaned_names.append(name)

    # Match names with records by position (1-to-1)
    num_pairs = min(len(cleaned_names), len(orphaned_records))
    for i in range(num_pairs):
        name = cleaned_names[i]
        record, _ = orphaned_records[i]
        points = calculate_points(record)
        standings.append({
            'rank': i + 1,  # Rank will be recalculated after sorting
            'name': name,
            'record': record,
            'points': points,
            'omw': None,
            'gw': None
        })

    # Handle unmatched records (more records than names)
    if len(orphaned_records) > num_pairs:
        for i in range(num_pairs, len(orphaned_records)):
            record, _ = orphaned_records[i]
            # Use a placeholder name - will be recovered by fuzzy matching later
            standings.append({
                'rank': i + 1,
                'name': f'Unknown_{i+1}',
                'record': record,
                'points': calculate_points(record),
                'omw': None,
                'gw': None
            })

    return standings if standings else None


def parse_standings_debug(ocr_text: str) -> tuple[List[Dict], dict]:  # type: ignore
    """Parse standings and return debug info about orphaned data."""
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    record_pattern = r'\d{1,2}-\d{1,2}(?:-\d{1,2})?'

    header_idx = -1
    for i, line in enumerate(lines):
        if 'RANK' in line.upper() and 'NAME' in line.upper():
            header_idx = i
            break

    if header_idx == -1:
        return [], {'orphaned_names': [], 'orphaned_records': [], 'complete_entries': 0}

    standings = []
    orphaned_records = []
    orphaned_names = []
    standalone_names = []
    standalone_ranks = []
    complete_count = 0

    for line in lines[header_idx + 1:]:
        line_upper = line.upper()

        if any(kw in line_upper for kw in ['STANDINGS', 'MATCH', 'ROUND', 'ASOF']):
            continue
        if line.startswith(('«', '>', '<', '◆', '♦', '●', '◉', '»', '~', ')')):
            continue
        if not line or len(line.strip()) < 1:
            continue

        # Fix misread rank digits - same logic as main parser
        line_fixed = line
        if len(line) > 1 and line[0] in 'OoIlZ':
            if line[0] in 'OoIl' and line[1].isdigit():
                line_fixed = '1' + line[1:]
            elif line[0] == 'O' and line[1] == ' ':
                line_fixed = '10 ' + line[2:].lstrip()
            elif line[0] in 'OoIl' and line[1] == ' ':
                line_fixed = '1 ' + line[2:].lstrip()
            else:
                ocr_to_digit = {'O': '0', 'o': '0', 'I': '1', 'l': '1', 'Z': '2'}
                if line[0] in ocr_to_digit:
                    line_fixed = ocr_to_digit[line[0]] + line[1:]

        rank_match = re.match(r'^(\d{1,2})[.\s]+', line_fixed)
        if not rank_match:
            records = re.findall(record_pattern, line)
            if records:
                orphaned_records.append(records[0])
                continue

            # Check if line is just a rank number
            if re.match(r'^\d{1,2}$', line.strip()):
                standalone_ranks.append(int(line.strip()))
                continue

            # Check if line is a name
            if any(c.isalpha() for c in line) and not re.search(r'\d{1,2}-\d{1,2}', line):
                name = clean_name(line)
                if name and len(name) > 1:
                    standalone_names.append(name)
                continue

            continue

        rank = int(rank_match.group(1))

        # Skip rank 0 or very high ranks (likely garbage/misread)
        if rank == 0 or rank > 50:
            continue

        line_without_rank = re.sub(r'^\d{1,2}[.\s]+', '', line_fixed).strip()

        records = re.findall(record_pattern, line)
        if not records:
            # Store just the name text, ignore the rank (we'll match by position instead)
            orphaned_names.append(line_without_rank)
            continue

        record = records[0]
        percents = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)

        name_candidate = line_without_rank
        for rec in records:
            name_candidate = name_candidate.replace(rec, '').strip()
        for perc in percents:
            name_candidate = name_candidate.replace(f"{perc}%", '').replace(perc, '').strip()
        name_candidate = re.sub(r'\s*\d+\s*(?=' + record_pattern + ')', '', name_candidate).strip()

        if name_candidate and len(name_candidate) > 1:
            name = clean_name(name_candidate)
            if name and len(name) > 1:
                points = calculate_points(record)
                omw = float(percents[0]) if len(percents) > 0 else None
                gw = float(percents[1]) if len(percents) > 1 else None
                standings.append({
                    'rank': rank,
                    'name': name,
                    'record': record,
                    'points': points,
                    'omw': omw,
                    'gw': gw
                })
                complete_count += 1

    return standings, {
        'orphaned_names': orphaned_names,
        'orphaned_records': orphaned_records,
        'standalone_names': standalone_names,
        'standalone_ranks': standalone_ranks,
        'complete_entries': complete_count
    }


def parse_standings_column_format(lines: List[str], record_pattern: str) -> Optional[List[Dict]]:
    """Try to parse column-based format with separate NAME, POINTS, OMW% sections."""
    names = []
    records_raw = []
    percentages = []

    in_name_section = False
    in_points_section = False
    in_omw_section = False

    for line in lines:
        line_upper = line.upper()

        if line_upper == 'NAME':
            in_name_section = True
            in_points_section = False
            in_omw_section = False
            continue
        elif 'POINTS' in line_upper and 'W-L-D' in line_upper:
            in_name_section = False
            in_points_section = True
            in_omw_section = False
            continue
        elif line_upper == 'OMW%':
            in_name_section = False
            in_points_section = False
            in_omw_section = True
            continue

        if any(kw in line_upper for kw in ['RANK', 'MATCH', 'STANDINGS', 'PLAYER', 'GW%', 'ASOF']):
            continue
        if line.startswith(('»', '>', '<', '◆', '♦', '●', '◉', '~')):
            continue
        if not line or len(line.strip()) < 2:
            continue

        if in_name_section:
            name = clean_name(line)
            if name and len(name) > 1:
                names.append(name)

        elif in_points_section:
            if re.search(record_pattern, line):
                records_raw.append(line)

        elif in_omw_section:
            percents = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)
            for p in percents:
                percentages.append(float(p))

    if not names and not records_raw:
        return None

    records = []
    for record_line in records_raw:
        parts = record_line.split()
        points = None
        record = None

        for i, part in enumerate(parts):
            if re.search(record_pattern, part):
                record = part.rstrip('.')
                if i > 0 and parts[i-1].isdigit():
                    points = int(parts[i-1])
                break

        if record:
            if not points:
                points = calculate_points(record)
            records.append({'record': record, 'points': points})

    standings = []
    num_entries = max(len(names), len(records))

    for idx in range(num_entries):
        name = names[idx] if idx < len(names) else f"Unknown_{idx+1}"

        if idx < len(records):
            record = records[idx]['record']
            points = records[idx]['points']
        else:
            continue

        omw = None
        if idx < len(percentages):
            omw = percentages[idx]

        standings.append({
            'rank': idx + 1,
            'name': name,
            'record': record,
            'points': points,
            'omw': omw,
            'gw': None
        })

    return standings if standings else None


def parse_standings(ocr_text: str) -> List[Dict]:
    """Parse standings from OCR text, trying both formats."""
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
    record_pattern = r'\d{1,2}-\d{1,2}(?:-\d{1,2})?'

    standings = parse_standings_table_format(lines, record_pattern)
    if standings:
        return standings

    standings = parse_standings_column_format(lines, record_pattern)
    if standings:
        return standings

    print("Warning: Could not parse standings in either format")
    return []


def merge_standings(all_standings: List[List[Dict]]) -> List[Dict]:
    """
    Merge standings from multiple screenshots, deduplicating by player name.
    Keeps the best (highest points) record for each player.
    Fills in missing percentages from different screenshots.
    Sorts by points (descending) and reassigns ranks.
    """
    merged = {}

    for standings in all_standings:
        for entry in standings:
            name = entry['name'].lower().strip()

            if name not in merged:
                merged[name] = entry.copy()
            else:
                # Keep the best (highest points) record
                if entry['points'] > merged[name]['points']:
                    merged[name]['points'] = entry['points']
                    merged[name]['record'] = entry['record']

                # Fill in missing percentages from other screenshots
                if merged[name]['omw'] is None and entry['omw'] is not None:
                    merged[name]['omw'] = entry['omw']
                if merged[name]['gw'] is None and entry['gw'] is not None:
                    merged[name]['gw'] = entry['gw']

    # Sort by points (descending), then GW%, then OMW%, then name
    # GW% and OMW% default to 0 if not present
    result = sorted(merged.values(), key=lambda x: (
        -x['points'],
        -(x['gw'] if x['gw'] is not None else 0),
        -(x['omw'] if x['omw'] is not None else 0),
        x['name']
    ))

    # Reassign ranks after sorting
    for idx, entry in enumerate(result, 1):
        entry['rank'] = idx

    return result


def add_week_to_entries(standings: List[Dict], week_date: str) -> List[Dict]:
    """Add week field to all entries."""
    for entry in standings:
        entry['week'] = week_date
    return standings


def write_excel(standings: List[Dict], output_path: str):
    """Write standings to Excel file."""
    if not standings:
        print("No data to write")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Standings"

    # Check if week field exists in any entry
    has_week = any('week' in entry for entry in standings)

    # Column order: Name, Record, Week (if present), Points, OMW%
    headers = ['Name', 'Record']
    if has_week:
        headers.append('Week')
    headers.append('Points')
    headers.append('OMW%')

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row_idx, entry in enumerate(standings, 2):
        col_idx = 1
        ws.cell(row=row_idx, column=col_idx).value = entry.get('name', '')
        col_idx += 1
        ws.cell(row=row_idx, column=col_idx).value = entry.get('record', '')
        col_idx += 1
        if has_week:
            ws.cell(row=row_idx, column=col_idx).value = entry.get('week', '')
            col_idx += 1
        ws.cell(row=row_idx, column=col_idx).value = entry.get('points', 0)
        col_idx += 1
        ws.cell(row=row_idx, column=col_idx).value = entry.get('omw', '')

    # Auto-adjust column widths
    ws.column_dimensions['A'].width = 20  # Name
    ws.column_dimensions['B'].width = 12  # Record
    if has_week:
        ws.column_dimensions['C'].width = 12  # Week
        ws.column_dimensions['D'].width = 10  # Points
        ws.column_dimensions['E'].width = 10  # OMW%
    else:
        ws.column_dimensions['C'].width = 10  # Points
        ws.column_dimensions['D'].width = 10  # OMW%

    wb.save(output_path)
    print(f"✓ Excel written: {output_path}")
    print(f"✓ Total entries: {len(standings)}")


def write_csv(standings: List[Dict], output_path: str):
    """Write standings to CSV file."""
    if not standings:
        print("No data to write")
        return

    # Check if week field exists in any entry
    has_week = any('week' in entry for entry in standings)

    # Column order: Name, Record, Week (if present), Points, OMW%
    headers = ['Name', 'Record']
    if has_week:
        headers.append('Week')
    headers.append('Points')
    headers.append('OMW%')

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for entry in standings:
            row = {
                'Name': entry.get('name', ''),
                'Record': entry.get('record', ''),
                'Points': entry.get('points', 0),
                'OMW%': entry.get('omw', '')
            }
            if has_week:
                row['Week'] = entry.get('week', '')
            writer.writerow(row)

    print(f"✓ CSV written: {output_path}")
    print(f"✓ Total entries: {len(standings)}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract MTG standings from screenshots (supports multiple files)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python screenshot_extract_v3.py screenshot.png
  python screenshot_extract_v3.py screenshot.png -d 9/14/26
  python screenshot_extract_v3.py img1.png img2.png -o merged.xlsx
  python screenshot_extract_v3.py img1.png img2.png -d 9/21/26 --debug
  python screenshot_extract_v3.py img1.png img2.png -f csv
  python screenshot_extract_v3.py img1.png img2.png -o standings.csv -f csv
        '''
    )
    parser.add_argument('images', nargs='+', help='Screenshot image file(s)')
    parser.add_argument('-o', '--output', help='Output file (default: standings_M_D_YY.xlsx or .csv with date)')
    parser.add_argument('-d', '--date', help='Week start date in M/D/YY format (default: current week Monday)')
    parser.add_argument('-f', '--format', choices=['xlsx', 'csv'], default='xlsx', help='Output format (default: xlsx)')
    parser.add_argument('--debug', action='store_true', help='Show debug output')

    args = parser.parse_args()

    # Determine week date
    week_date = args.date if args.date else get_week_start_date()

    all_standings = []

    for image_path in args.images:
        if not os.path.exists(image_path):
            print(f"Error: File not found: {image_path}")
            sys.exit(1)

        print(f"Processing: {image_path}")

        ocr_text = extract_ocr_text(image_path)

        if args.debug:
            print(f"\n=== Raw OCR Output ({image_path}) ===")
            print(ocr_text)
            print("======================\n")

        if args.debug:
            standings, debug_info = parse_standings_debug(ocr_text)
            print(f"Debug: Extracted {len(standings)} complete entries from {image_path}")
            print(f"  Complete entries: {debug_info['complete_entries']}")
            print(f"  Orphaned names: {len(debug_info['orphaned_names'])} - {debug_info['orphaned_names']}")
            print(f"  Orphaned records: {len(debug_info['orphaned_records'])} - {debug_info['orphaned_records']}")
            print(f"  Standalone names: {len(debug_info['standalone_names'])} - {debug_info['standalone_names']}")
            print(f"  Standalone ranks: {len(debug_info['standalone_ranks'])} - {debug_info['standalone_ranks']}")
            for entry in standings[:3]:
                print(f"    {entry}")
        else:
            standings = parse_standings(ocr_text)

        all_standings.append(standings)

    # Merge all standings and deduplicate
    merged_standings = merge_standings(all_standings)

    # Add week field to all entries
    merged_standings = add_week_to_entries(merged_standings, week_date)

    # Recover unknown names using known player list
    all_extracted_names = []
    for standings in all_standings:
        for entry in standings:
            all_extracted_names.append(entry['name'])
    merged_standings = recover_unknowns(merged_standings, all_extracted_names)

    if args.debug:
        print(f"\nDebug: After merge and dedup: {len(merged_standings)} unique entries")

    # Determine output filename if not specified
    if args.output:
        output_file = args.output
    else:
        # Auto-generate filename with appropriate extension
        week_date_formatted = week_date.replace('/', '_')
        ext = 'csv' if args.format == 'csv' else 'xlsx'
        output_file = f'standings_{week_date_formatted}.{ext}'

    # Write output in specified format
    if args.format == 'csv':
        write_csv(merged_standings, output_file)
    else:
        write_excel(merged_standings, output_file)


if __name__ == '__main__':
    main()
