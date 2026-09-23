#!/usr/bin/env python3
"""
Simplified Magic: The Gathering Tournament Standings Extractor v2

Cleaner approach focusing on robust multi-column table parsing.
Works with screenshots where names, records, and percentages are in separate columns.
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
    """Apply basic contrast/sharpness enhancement."""
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
    draws = int(match.group(3)) or 0
    return wins * 3 + draws * 1


def parse_standings(ocr_text: str) -> List[Dict]:
    """
    Parse standings from OCR text.

    Handles multi-column layout:
    - Extract all names (after NAME header)
    - Extract all records (after POINTS header)
    - Extract all percentages (after OMW% header)
    - Match by index position
    """
    lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]

    names = []
    records_raw = []
    percentages = []

    # State tracking
    in_name_section = False
    in_points_section = False
    in_omw_section = False

    record_pattern = r'\d{1,2}-\d{1,2}(?:-\d{1,2})?'

    for line in lines:
        line_upper = line.upper()

        # Track sections
        if line_upper == 'NAME':
            in_name_section = True
            in_points_section = False
            in_omw_section = False
            continue
        elif any(kw in line_upper for kw in ['POINTS', 'POINTS W-L-D']):
            in_name_section = False
            in_points_section = True
            in_omw_section = False
            continue
        elif line_upper == 'OMW%':
            in_name_section = False
            in_points_section = False
            in_omw_section = True
            continue

        # Skip headers/metadata
        if any(kw in line_upper for kw in ['RANK', 'MATCH', 'STANDINGS', 'PLAYER', 'W-L-D', 'GW%', 'ASOF']):
            continue
        if line.startswith(('»', '>', '<', '◆', '♦', '●', '◉')):
            continue

        # Extract based on section
        if in_name_section:
            name = clean_name(line)
            if name and not any(c.isdigit() for c in line[:3]):  # Skip digit-heavy lines
                names.append(name)

        elif in_points_section:
            # Extract record and points from lines like "9 3-0-0" or just "3-0-0"
            if re.search(record_pattern, line):
                records_raw.append(line)

        elif in_omw_section:
            # Extract percentages
            percents = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)
            for p in percents:
                percentages.append(float(p))

    # Parse records to extract points and record
    records = []
    for record_line in records_raw:
        parts = record_line.split()
        points = None
        record = None

        # Find the record pattern
        for i, part in enumerate(parts):
            if re.search(record_pattern, part):
                record = part.rstrip('.')
                # Check if there's a digit before it (points)
                if i > 0 and parts[i-1].isdigit():
                    points = int(parts[i-1])
                break

        if record:
            if not points:
                points = calculate_points(record)
            records.append({'record': record, 'points': points})

    # Match names with records and percentages by index
    standings = []
    num_entries = max(len(names), len(records))

    for idx in range(num_entries):
        name = names[idx] if idx < len(names) else f"Unknown_{idx+1}"

        if idx < len(records):
            record = records[idx]['record']
            points = records[idx]['points']
        else:
            continue  # Skip if no record

        # Match percentages (typically 1 per entry)
        omw = None
        if idx < len(percentages):
            omw = percentages[idx]

        standings.append({
            'name': name,
            'record': record,
            'points': points,
            'omw': omw,
            'rank': idx + 1
        })

    return standings


def write_excel(standings: List[Dict], output_path: str):
    """Write standings to Excel file."""
    if not standings:
        print("No data to write")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Standings"

    # Headers
    headers = ['Rank', 'Name', 'Record', 'Points', 'OMW%']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Data
    for row_idx, entry in enumerate(standings, 2):
        ws.cell(row=row_idx, column=1).value = entry.get('rank')
        ws.cell(row=row_idx, column=2).value = entry.get('name', '')
        ws.cell(row=row_idx, column=3).value = entry.get('record', '')
        ws.cell(row=row_idx, column=4).value = entry.get('points', 0)
        ws.cell(row=row_idx, column=5).value = entry.get('omw', '')

    # Auto-adjust widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 10

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

    # Extract OCR text
    ocr_text = extract_ocr_text(args.image)

    if args.debug:
        print("\n=== Raw OCR Output ===")
        print(ocr_text)
        print("======================\n")

    # Parse standings
    standings = parse_standings(ocr_text)

    if args.debug:
        print(f"Debug: Extracted {len(standings)} entries")
        for entry in standings[:3]:
            print(f"  {entry}")

    # Write output
    output_file = args.output or f"standings_extract_v2.xlsx"
    write_excel(standings, output_file)


if __name__ == '__main__':
    main()
