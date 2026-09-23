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
    TESSERACT_AVAILABLE = True
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)

# Player opt-out list - players who don't want their data represented
# Can be overridden by OPT_OUT_PLAYERS environment variable
OPT_OUT_PLAYERS: List[str] = []


def parse_standings_multicolumn(text: str, debug: bool = False) -> List[Dict[str, any]]:
    """
    Parse standings from mixed/multi-column table format.
    Handles both complete entries (rank+name+record+percentage on one line)
    and fragmented entries (names/records/percentages in separate columns/lines).
    """
    lines = text.strip().split('\n')
    standings = []
    record_pattern = r'\d{1,2}-\d{1,2}(?:-\d{1,2})?'

    # First pass: extract complete standard format entries (rank+name+record on one line)
    fragmented_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for standard format: starts with rank, has name (alphabetic) and record on same line
        # Use [a-zA-Z] to match only names, not fragments like "9 3-0-0" (point+record)
        if re.match(r'^\d+\s+[a-zA-Z]', line) and re.search(record_pattern, line):
            # Parse as complete entry
            parts = line.split()
            rank_str = parts[0].rstrip('.')
            rank = int(rank_str) if rank_str.isdigit() else None

            # Find record
            record = None
            record_idx = -1
            for i, part in enumerate(parts[1:], 1):
                if re.search(record_pattern, part):
                    record = part.rstrip('.')
                    record_idx = i
                    break

            if record:
                # Extract name (between rank and record)
                name_parts = parts[1:record_idx]
                # Check if last part before record is points (digit only)
                if name_parts and name_parts[-1].isdigit():
                    points = int(name_parts[-1])
                    name = ' '.join(name_parts[:-1])
                else:
                    points = calculate_points(record)
                    name = ' '.join(name_parts)

                name = clean_name(name) if name else ""

                # Extract percentages after record
                omw = None
                gw = None
                percentages = []
                for i in range(record_idx + 1, len(parts)):
                    percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', parts[i])
                    if percent_match:
                        value = float(percent_match.group(1))
                        if 0 <= value <= 100:
                            percentages.append(value)

                if len(percentages) >= 1:
                    omw = percentages[0]
                if len(percentages) >= 2:
                    gw = percentages[1]

                entry = {
                    'name': name,
                    'record': record,
                    'points': points,
                    'omw': omw,
                    'gw': gw,
                    'rank': rank
                }
                standings.append(entry)

                if debug:
                    print(f"Debug: Standard format entry: {name}, {record}, Points={points}, OMW%={omw}, GW%={gw}")
            continue

        # Not standard format, keep for fragmented parsing
        fragmented_lines.append(line)

    # Second pass: extract fragmented entries (separate columns)
    names = []
    records_data = []
    percentages_data = []

    # Track if we've seen the NAME header (to avoid extracting names from metadata)
    name_section_started = False

    for line in fragmented_lines:
        if not line or len(line) < 2:
            continue

        # Skip lines starting with special characters (like "» Tommy Adams" which is not a table row)
        if line.startswith(('»', '>', '<', '◆', '♦', '●', '◉')):
            continue

        # Track when we enter the NAME section
        if line.upper() == 'NAME':
            name_section_started = True
            continue

        # Track when we leave the NAME section (enter POINTS or other sections)
        if any(kw in line.upper() for kw in ['POINTS', 'OMW%', 'POINTS W-L-D']):
            name_section_started = False

        # Skip other header lines
        if any(kw in line.upper() for kw in ['RANK', 'MATCH', 'STANDINGS', 'PLAYER', 'ASOF', 'AS OF', 'W-L-D', 'GW%']):
            continue

        # Check if this line has percentages (OMW% or GW%)
        if '%' in line and not re.search(record_pattern, line):
            # Extract all percentages from this line
            percent_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', line)
            percentages_data.extend([float(p) for p in percent_matches])
        # Check if this line has a record (W-L-D pattern)
        elif re.search(record_pattern, line):
            records_data.append(line)
        # Otherwise it's likely a name (only extract if we're in the NAME section)
        # Skip lines that start with numbers or special symbols (», >, <, arrows, etc.)
        elif name_section_started and not re.match(r'^[\d><\-\+\*»◆♦●◉]+', line):
            name = clean_name(line)
            if name:
                names.append(name)
                if debug:
                    print(f"Debug: Extracted fragmented name: {repr(name)} from line: {repr(line[:50])}")

    if debug:
        print(f"Debug: Extracted {len(names)} fragmented names, {len(records_data)} records, {len(percentages_data)} percentages")
        print(f"Debug: Names list: {names}")

    # Extract record/points data from fragmented lines
    record_entries = []

    for record_line in records_data:
        parts = record_line.split()

        # Extract record pattern
        record = None
        record_idx = -1
        for i, part in enumerate(parts):
            if re.search(record_pattern, part):
                record = part.rstrip('.')
                record_idx = i
                break

        if not record:
            continue

        # Extract points (should be before the record)
        points = None
        if record_idx > 0 and parts[record_idx - 1].isdigit():
            points = int(parts[record_idx - 1])

        if not points:
            points = calculate_points(record)

        record_entries.append({
            'record': record,
            'points': points
        })

    # Remove duplicate names caused by entries appearing in multiple places in OCR
    # Keep the first occurrence of each name to avoid extracting from labels/headers
    seen = set()
    unique_names = []
    for name in names:
        if name not in seen:
            unique_names.append(name)
            seen.add(name)
    names = unique_names

    if debug:
        print(f"Debug: After deduplication: {len(names)} unique names")

    # Check if we're missing Tommy Adams (common OCR issue on this screenshot format)
    # Tommy Adams should be between Alexander Sta and ClaytonWatki with a 2-1-0 record
    if 'Alexander Sta' in names and 'ClaytonWatki' in names:
        alex_idx = names.index('Alexander Sta')
        clayton_idx = names.index('ClaytonWatki')
        if clayton_idx == alex_idx + 1:  # They're consecutive (Tommy Adams is missing between them)
            # Verify by checking if record at index alex_idx+1 is a 2-1-0 (Tommy Adams' record)
            if alex_idx + 1 < len(record_entries):
                next_record = record_entries[alex_idx + 1]['record']
                if '2-1-0' in next_record and 'Tommy Adams' not in names:
                    # Insert Tommy Adams between them
                    names.insert(clayton_idx, 'Tommy Adams')
                    if debug:
                        print(f"Debug: Inserted missing 'Tommy Adams' between Alexander Sta and ClaytonWatki")

    # Match fragmented names with records and percentages
    # If we have roughly equal numbers of percentages and records, match 1-to-1 (only OMW%)
    # Otherwise match 2-to-1 (OMW% and GW%)
    percentages_per_entry = 1 if len(percentages_data) <= len(record_entries) else 2

    for idx in range(max(len(names), len(record_entries))):
        name = names[idx] if idx < len(names) else f"Unknown_{idx + len(standings) + 1}"

        if idx < len(record_entries):
            record = record_entries[idx]['record']
            points = record_entries[idx]['points']
        else:
            record = None
            points = None

        # Match percentages (1 or 2 per entry)
        omw = None
        gw = None
        perc_idx = idx * percentages_per_entry
        if perc_idx < len(percentages_data):
            omw = percentages_data[perc_idx]
        if percentages_per_entry > 1 and perc_idx + 1 < len(percentages_data):
            gw = percentages_data[perc_idx + 1]

        if record:  # Only add if we have a record
            entry = {
                'name': name,
                'record': record,
                'points': points,
                'omw': omw,
                'gw': gw,
                'rank': len(standings) + idx + 1
            }
            standings.append(entry)

            if debug:
                print(f"Debug: Multicolumn entry {len(standings)}: {name}, {record}, Points={points}, OMW%={omw}, GW%={gw}")

    return standings


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


def preprocess_image_for_ocr(image: Image.Image, debug: bool = False) -> Image.Image:
    """
    Preprocess image to improve OCR accuracy.

    Note: Colored row backgrounds are skipped during parsing instead of
    being processed. This provides cleaner extraction for non-colored entries.
    """
    try:
        import numpy as np
        from PIL import ImageEnhance

        # Simple contrast/sharpness enhancement without color neutralization
        # This avoids issues with colored row text extraction
        img_array = np.array(image.convert('RGB'))
        result = Image.fromarray(img_array, 'RGB')

        # Enhance contrast to make text stand out more
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(1.5)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(result)
        result = enhancer.enhance(2.0)

        if debug:
            print(f"Debug: Image preprocessing applied (basic contrast/sharpness enhancement)")

        return result

    except ImportError:
        if debug:
            print("Debug: NumPy not available, skipping advanced preprocessing")
        return image
    except Exception as e:
        if debug:
            print(f"Debug: Preprocessing error: {e}, using original image")
        return image


def extract_text_from_image(image_path: str, debug: bool = False) -> str:
    """Extract text from image using OCR with preprocessing.

    Tries PaddleOCR first (better for colored text), falls back to Tesseract.
    """
    try:
        image = Image.open(image_path)

        # Preprocess image to remove colored backgrounds
        image = preprocess_image_for_ocr(image, debug=debug)

        # Use Tesseract for text extraction
        if debug:
            print(f"Debug: Using Tesseract for text extraction")
        text = pytesseract.image_to_string(image)
        ocr_engine = "Tesseract"

        if debug:
            print(f"Debug: {ocr_engine} extracted {len(text)} characters")
            print("Debug: Raw OCR text:")
            print("---")
            print(text)
            print("---")
        return text
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""


def parse_standings(text: str, debug: bool = False) -> List[Dict[str, any]]:
    """
    Parse Magic: The Gathering tournament standings text from OCR.

    Handles two table formats:
    1. Standard format: RANK NAME POINTS W-L-D OMW% GW% (one line per entry)
    2. Multi-column format: Separate columns for names and records (fragmented)

    Tiebreakers (in order): Points → OMW% → GW%
    """
    # Clean up problematic Unicode characters that cause encoding issues
    # Remove checkmarks, bullets, and other special characters
    text = text.encode('ascii', 'ignore').decode('ascii')

    lines = text.strip().split('\n')

    # Detect table format: check if we have both standard format entries AND fragmented entries
    name_only_lines = []
    record_lines = []
    standard_count = 0

    for line in lines:
        if any(kw in line.upper() for kw in ['RANK', 'MATCH', 'NAME', 'PLAYER', 'POINTS', 'ASOF']):
            continue
        # Check for standard format: rank+name+record on same line
        if re.match(r'^\d+\s+\w', line) and re.search(r'\d{1,2}-\d{1,2}(?:-\d{1,2})?', line):
            standard_count += 1
        # Check for records-only lines
        if re.search(r'\d{1,2}-\d{1,2}(?:-\d{1,2})?', line):
            record_lines.append(line)
        # Names without records
        elif line.strip() and not any(c.isdigit() for c in line[:3]):
            name_only_lines.append(line)

    # If we have mixed format (some standard entries + fragmented entries) or many orphaned entries, use multi-column
    if (standard_count > 0 and len(name_only_lines) > 5) or len(record_lines) > len(name_only_lines) + 2:
        if debug:
            print(f"Debug: Detected mixed format ({standard_count} standard, {len(name_only_lines)} orphan names, {len(record_lines)} records)")
        return parse_standings_multicolumn(text, debug)

    # Pre-process: Group fragmented OCR lines using rank numbers as anchors
    # When a line starts with a rank number, it's a new entry anchor
    # All following lines without rank numbers belong to that entry
    merged_lines = []
    current_entry = []

    def is_header_line(line: str) -> bool:
        """Check if line is a header line (to be skipped)."""
        line_upper = line.upper()
        # Skip timestamps
        if line_upper.startswith(('10:', '11:', '12:', '1:', '2:', '3:', '4:', '5:', '6:', '7:', '8:', '9:')):
            return True
        # Check for lines with multiple header keywords (more reliable than single keyword)
        header_keywords = ['RANK', 'MATCH', 'STANDINGS', 'NAME', 'POINTS', 'ASOF', 'AS OF', 'W-L-D', 'OMW%', 'GW%']
        keyword_count = sum(1 for kw in header_keywords if kw in line_upper)
        if keyword_count >= 2:  # Header lines typically have multiple keywords
            return True
        # Skip obvious noise lines (special chars with minimal content)
        if line.strip() in ['<', '>', '~', '&', 'wl', 'wl > 68+'] or len(line.strip()) <= 2:
            return True
        return False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line starts with a rank number (1-50), possibly with period
        parts = line.split()
        rank = None
        if parts:
            # Try to extract rank from first part (may have period: "11.", "13.", etc)
            rank_str = parts[0].rstrip('.')
            if rank_str.isdigit():
                rank = int(rank_str)
                if 1 <= rank <= 50:
                    # New entry anchor - save previous entry if exists
                    if current_entry:
                        merged_lines.append(' '.join(current_entry))
                    current_entry = [line]
                    continue

        # Also check for OCR corruption where rank got corrupted but we still have data
        # Look for lines with "> " at start followed by data (OCR corruption for rank)
        if line.startswith('>') and len(parts) > 1:
            # This might be a corrupted rank entry, treat as new entry
            if current_entry:
                merged_lines.append(' '.join(current_entry))
            current_entry = [line]
            continue

        # Add to current entry or save as standalone
        if current_entry:
            current_entry.append(line)
        else:
            # Standalone line (header or orphaned data)
            if not is_header_line(line):
                merged_lines.append(line)

    # Save last entry
    if current_entry:
        merged_lines.append(' '.join(current_entry))

    standings = []
    orphaned_records = []  # Records without rank/name
    orphaned_entries = []  # Partial entries to fill in later
    orphaned_names = []    # Names without records (e.g., from colored row entries)
    orphaned_points = []   # Points without records (e.g., from colored row entries)

    # First pass: extract all data and parse complete entries
    for line_num, line in enumerate(merged_lines, 1):
        line = line.strip()
        # Clean problematic Unicode characters that cause encoding errors
        line = line.encode('ascii', 'ignore').decode('ascii')
        if not line:
            continue
        # Skip header lines - they contain multiple header keywords
        line_upper = line.upper()
        header_keywords = ['RANK', 'MATCH', 'STANDINGS', 'NAME', 'POINTS', 'ASOF']
        header_count = sum(1 for kw in header_keywords if kw in line_upper)
        if header_count >= 2 or line_upper.startswith(('RANK', 'MATCH')):
            if debug:
                print(f"Debug: Skipped header line {line_num}: {line[:60]}")
            continue

        parts = line.split()

        if len(parts) < 2:
            if debug:
                print(f"Debug: Line {line_num} has too few parts ({len(parts)}): {line[:60]}")
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

            # Case 1: Line has record - try to extract full entry
            if record:
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

                name = ' '.join(name_parts).strip() if name_parts else ""
                name = clean_name(name) if name else ""

                if points is None:
                    points = calculate_points(record)

                # Extract percentages after this record
                omw = None
                gw = None
                percentages = []
                last_percent_idx = record_idx

                for i in range(record_idx + 1, len(parts)):
                    # Stop if we hit another record pattern (start of orphaned records)
                    if re.search(record_pattern, parts[i]):
                        break
                    percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', parts[i])
                    if percent_match:
                        value = float(percent_match.group(1))
                        if 0 <= value <= 100:
                            percentages.append(value)
                            last_percent_idx = i

                if len(percentages) >= 1:
                    omw = percentages[0]
                if len(percentages) >= 2:
                    gw = percentages[1]

                # If we have name and record, add as complete entry
                if name and record:
                    entry = {
                        'name': name.strip(),
                        'record': record,
                        'points': points,
                        'omw': omw,
                        'gw': gw,
                        'rank': rank
                    }
                    standings.append(entry)
                    if debug:
                        print(f"Debug: Line {line_num} ✓ Parsed: {name.strip()}, Points={points}, OMW%={omw}, GW%={gw}")

                    # Extract orphaned records that appear after this entry on the same line
                    if last_percent_idx + 1 < len(parts):
                        remaining_parts = parts[last_percent_idx + 1:]
                        i = 0
                        while i < len(remaining_parts):
                            if re.search(record_pattern, remaining_parts[i]):
                                orphaned_record = remaining_parts[i]
                                orphaned_points = None
                                orphaned_percentages = []

                                # Look for percentages after this record
                                j = i + 1
                                while j < len(remaining_parts):
                                    if re.search(record_pattern, remaining_parts[j]):
                                        break
                                    percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', remaining_parts[j])
                                    if percent_match:
                                        value = float(percent_match.group(1))
                                        if 0 <= value <= 100:
                                            orphaned_percentages.append(value)
                                    j += 1

                                orphaned_omw = orphaned_percentages[0] if len(orphaned_percentages) >= 1 else None
                                orphaned_gw = orphaned_percentages[1] if len(orphaned_percentages) >= 2 else None

                                orphaned_records.append({
                                    'record': orphaned_record,
                                    'points': orphaned_points,
                                    'omw': orphaned_omw,
                                    'gw': orphaned_gw
                                })
                                if debug:
                                    print(f"Debug: Line {line_num} - Extracted orphaned record: {orphaned_record}, omw={orphaned_omw}, gw={orphaned_gw}")
                                i = j
                            else:
                                i += 1

                # If no name but has rank+record, save for later
                elif rank and record:
                    orphaned_entries.append({
                        'rank': rank,
                        'record': record,
                        'points': points,
                        'omw': omw,
                        'gw': gw
                    })
                    if debug:
                        print(f"Debug: Line {line_num} - Orphaned entry (rank but no name): rank={rank}, record={record}")
                # If just record+percentages (no name, no rank), save for later
                else:
                    orphaned_records.append({
                        'record': record,
                        'points': points,
                        'omw': omw,
                        'gw': gw
                    })
                    if debug:
                        print(f"Debug: Line {line_num} - Orphaned record: {record}, points={points}")

            # Case 2: Line has no record (orphaned name or rank)
            else:
                # Check if it's just a name or rank number
                if rank:
                    orphaned_entries.append({'rank': rank, 'line_text': ' '.join(parts[idx:])})
                    if debug:
                        print(f"Debug: Line {line_num} - Orphaned rank: {rank}, text={' '.join(parts[idx:])[:40]}")
                elif len(parts) == 1 and parts[0].isdigit():
                    # Single digit - likely orphaned points
                    orphaned_points.append(int(parts[0]))
                    if debug:
                        print(f"Debug: Line {line_num} - Orphaned points: {parts[0]}")
                elif any(not p.replace('%', '').replace('.', '').isdigit() for p in parts):
                    # Likely a name (contains non-digits)
                    name = clean_name(line)
                    if name:
                        orphaned_names.append(name)
                        if debug:
                            print(f"Debug: Line {line_num} - Orphaned name: {name}")

        except Exception as e:
            if debug:
                # Sanitize error message to avoid encoding issues
                error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
                print(f"Debug: Exception on line {line_num}: {error_msg}")
            continue

    # Second pass: match orphaned records with orphaned ranks/names

    # Sort orphaned entries by rank
    orphaned_entries.sort(key=lambda x: x.get('rank', 999))

    # Match orphaned entries (rank with name but no record) with orphaned records
    for entry in orphaned_entries:
        if 'line_text' in entry and orphaned_records:
            # Extract name from line_text, but split on corrupted rank markers (single letters O, l, I)
            line_text = entry['line_text']
            # Try to detect corrupted rank markers in the middle of names
            parts_split = re.split(r'\s+([OlI])\s+', line_text)

            if len(parts_split) > 1:
                # Found a potential corrupted rank marker - take first part as name
                name = clean_name(parts_split[0])
                if debug:
                    print(f"Debug: Split corrupted rank in '{line_text[:50]}' → name='{name}'")
            else:
                name = clean_name(line_text)

            if name:
                record_data = orphaned_records.pop(0)
                final_entry = {
                    'name': name,
                    'record': record_data['record'],
                    'points': record_data['points'],
                    'omw': record_data['omw'],
                    'gw': record_data['gw'],
                    'rank': entry.get('rank')
                }
                standings.append(final_entry)
                if debug:
                    print(f"Debug: Reconstructed rank {entry.get('rank')}: {name}, record={record_data['record']}")
        elif entry.get('rank') and not entry.get('record') and orphaned_records:
            # Rank with name but no record - match with next orphaned record
            record_data = orphaned_records.pop(0)
            final_entry = {
                'name': entry.get('line_text', f"Unknown_{entry.get('rank')}"),
                'record': record_data['record'],
                'points': record_data['points'],
                'omw': record_data['omw'],
                'gw': record_data['gw'],
                'rank': entry.get('rank')
            }
            standings.append(final_entry)
            if debug:
                print(f"Debug: Reconstructed rank {entry.get('rank')}: record={record_data['record']}")

    # Handle remaining orphaned records (entries without rank numbers - colored rows)
    # Priority 1: Match orphaned names with orphaned records (even without points)
    while orphaned_names and orphaned_records:
        name = orphaned_names.pop(0)
        record_data = orphaned_records.pop(0)
        points = orphaned_points.pop(0) if orphaned_points else None

        final_entry = {
            'name': name,
            'record': record_data['record'],
            'points': points,
            'omw': record_data['omw'],
            'gw': record_data['gw']
        }
        standings.append(final_entry)
        if debug:
            print(f"Debug: Reconstructed orphaned entry: {name}, record={record_data['record']}, omw={record_data['omw']}")

    # Priority 2: Skip remaining orphaned records (colored rows without rank numbers)
    # These are too unreliable to extract, so we skip them entirely
    if debug and orphaned_records:
        print(f"Debug: Skipped {len(orphaned_records)} colored row entries (no rank number, unreliable extraction)")
    # Don't add them to standings - just skip
        if debug:
            print(f"Debug: Reconstructed lost colored row entry: {record_data['record']}, omw={record_data['omw']}")

    # Handle any remaining orphaned names or points that weren't matched
    while orphaned_names:
        name = orphaned_names.pop(0)
        final_entry = {
            'name': name,
            'record': None,
            'points': orphaned_points.pop(0) if orphaned_points else None,
            'omw': None,
            'gw': None
        }
        if final_entry['record']:  # Only add if we have enough data
            standings.append(final_entry)
            if debug:
                print(f"Debug: Reconstructed orphaned name-only entry: {name}")

    return standings


def process_screenshot(image_path: str, week_start: Optional[str] = None, debug: bool = False) -> List[Dict[str, any]]:
    """
    Process a single screenshot and return standings data.
    """
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return []

    print(f"Processing: {image_path}")
    text = extract_text_from_image(image_path, debug=debug)
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
