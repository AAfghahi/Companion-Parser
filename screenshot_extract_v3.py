#!/usr/bin/env python3
"""
Magic: The Gathering Tournament Standings Extractor v3

Robust parser handling scrambled table OCR layouts where columns are interleaved.
- Table format: Can handle OCR text with rows/columns in mixed order
- Column format: Separate NAME, POINTS, OMW% sections
"""

import argparse
import os
import sys
from pathlib import Path
import re
from typing import List, Dict, Optional

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
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
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


def calculate_points(record: str) -> int:
    """Calculate points: Win=3, Loss=0, Draw=1."""
    match = re.search(r'(\d+)-(\d+)(?:-(\d+))?', record)
    if not match:
        return 0
    wins = int(match.group(1))
    losses = int(match.group(2))
    draws = int(match.group(3)) if match.group(3) else 0
    return wins * 3 + draws * 1


def parse_standings_table_format(lines: List[str], record_pattern: str) -> Optional[List[Dict]]:
    """Parse scrambled table format by extracting all data pieces separately."""

    header_idx = -1
    for i, line in enumerate(lines):
        if 'RANK' in line.upper() and 'NAME' in line.upper():
            header_idx = i
            break

    if header_idx == -1:
        return None

    # Extract all data pieces separately
    ranks = []
    names = []
    records = []
    percentages = []

    for line in lines[header_idx + 1:]:
        line_upper = line.upper()

        # Skip metadata lines
        if any(kw in line_upper for kw in ['STANDINGS', 'MATCH', 'ROUND', 'ASOF']):
            continue
        if line.startswith(('«', '>', '<', '◆', '♦', '●', '◉', '»', '~', ')')):
            continue
        if not line or len(line.strip()) < 2:
            continue

        # Extract ranks (1-2 digits at start)
        rank_match = re.match(r'^(\d{1,2})[.\s]', line)
        if rank_match:
            ranks.append(int(rank_match.group(1)))

        # Extract records (W-L or W-L-D format)
        found_record = re.search(record_pattern, line)
        if found_record:
            records.append(found_record.group(0))

        # Extract percentages
        percents = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)
        for p in percents:
            percentages.append(float(p))

        # Extract names (lines with letters that aren't just metadata)
        if not re.search(record_pattern, line) and not re.search(r'\d+\s*%', line):
            name_candidate = line.strip()

            # Skip if mostly numbers or special chars
            if name_candidate and any(c.isalpha() for c in name_candidate):
                # Remove leading rank number
                name_candidate = re.sub(r'^\d+[.\s]*', '', name_candidate).strip()
                # Remove trailing special chars and numbers
                name_candidate = re.sub(r'[)\]"\'~].*$', '', name_candidate).strip()

                if name_candidate and len(name_candidate) > 1:
                    cleaned = clean_name(name_candidate)
                    if cleaned and len(cleaned) > 1:
                        names.append(cleaned)

    # Match data by index
    num_entries = max(len(ranks), len(records))
    if num_entries == 0:
        return None

    standings = []
    for idx in range(num_entries):
        rank = ranks[idx] if idx < len(ranks) else idx + 1
        name = names[idx] if idx < len(names) else f"Unknown_{idx+1}"

        if idx < len(records):
            record = records[idx]
            points = calculate_points(record)
        else:
            continue

        omw = None
        if idx < len(percentages):
            omw = percentages[idx]

        standings.append({
            'rank': rank,
            'name': name,
            'record': record,
            'points': points,
            'omw': omw,
            'gw': None
        })

    return standings if standings else None


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


def write_excel(standings: List[Dict], output_path: str):
    """Write standings to Excel file."""
    if not standings:
        print("No data to write")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Standings"

    headers = ['Rank', 'Name', 'Record', 'Points', 'OMW%', 'GW%']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for row_idx, entry in enumerate(standings, 2):
        ws.cell(row=row_idx, column=1).value = entry.get('rank')
        ws.cell(row=row_idx, column=2).value = entry.get('name', '')
        ws.cell(row=row_idx, column=3).value = entry.get('record', '')
        ws.cell(row=row_idx, column=4).value = entry.get('points', 0)
        ws.cell(row=row_idx, column=5).value = entry.get('omw', '')
        ws.cell(row=row_idx, column=6).value = entry.get('gw', '')

    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 10

    wb.save(output_path)
    print(f"✓ Excel written: {output_path}")
    print(f"✓ Total entries: {len(standings)}")


def main():
    parser = argparse.ArgumentParser(description='Extract MTG standings from screenshots')
    parser.add_argument('image', help='Screenshot image file')
    parser.add_argument('-o', '--output', help='Output Excel file')
    parser.add_argument('--debug', action='store_true', help='Show debug output')

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"Error: File not found: {args.image}")
        sys.exit(1)

    print(f"Processing: {args.image}")

    ocr_text = extract_ocr_text(args.image)

    if args.debug:
        print("\n=== Raw OCR Output ===")
        print(ocr_text)
        print("======================\n")

    standings = parse_standings(ocr_text)

    if args.debug:
        print(f"Debug: Extracted {len(standings)} entries")
        for entry in standings[:5]:
            print(f"  {entry}")

    output_file = args.output or "standings_extract_v3.xlsx"
    write_excel(standings, output_file)


if __name__ == '__main__':
    main()
