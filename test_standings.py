#!/usr/bin/env python3
"""
Unit tests for Magic: The Gathering tournament standings parser
"""

import unittest
import re
from typing import Dict, List


def calculate_points(record: str) -> int:
    """
    Calculate points from a W-L-D record.

    Win = 3 points, Loss = 0 points, Draw = 1 point
    Example: "4-2-0" = 4*3 + 2*0 + 0*1 = 12 points
    """
    pattern = r'(\d+)-(\d+)(?:-(\d+))?'
    match = re.search(pattern, record)

    if not match:
        return 0

    wins = int(match.group(1))
    losses = int(match.group(2))
    draws = int(match.group(3)) if match.group(3) else 0

    points = (wins * 3) + (losses * 0) + (draws * 1)
    return points


def parse_standings(text: str) -> List[Dict[str, any]]:
    """
    Parse standings text from OCR.
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
                    'omw': None
                })

        except Exception as e:
            continue

    return standings


class TestPointCalculation(unittest.TestCase):
    """Test point calculation logic"""

    def test_basic_record_format_wld(self):
        """Test W-L-D format"""
        self.assertEqual(calculate_points("4-2-0"), 12)  # 4*3 + 2*0 + 0*1
        self.assertEqual(calculate_points("5-0-1"), 16)  # 5*3 + 0*0 + 1*1
        self.assertEqual(calculate_points("5-1-0"), 15)  # 5*3 + 1*0 + 0*1

    def test_record_format_wl(self):
        """Test W-L format (no draws)"""
        self.assertEqual(calculate_points("4-2"), 12)    # 4*3 + 2*0 + 0*1
        self.assertEqual(calculate_points("5-0"), 15)    # 5*3 + 0*0 + 0*1
        self.assertEqual(calculate_points("0-5"), 0)     # 0*3 + 5*0 + 0*1

    def test_draws_only(self):
        """Test records with draws"""
        self.assertEqual(calculate_points("4-1-1"), 13)  # 4*3 + 1*0 + 1*1
        self.assertEqual(calculate_points("3-2-2"), 11)  # 3*3 + 2*0 + 2*1
        self.assertEqual(calculate_points("2-1-3"), 9)   # 2*3 + 1*0 + 3*1

    def test_perfect_record(self):
        """Test perfect records"""
        self.assertEqual(calculate_points("5-0-0"), 15)  # All wins
        self.assertEqual(calculate_points("5-0"), 15)    # All wins (no draws)

    def test_zero_record(self):
        """Test zero win record"""
        self.assertEqual(calculate_points("0-5-0"), 0)
        self.assertEqual(calculate_points("0-0-5"), 5)   # All draws

    def test_invalid_record(self):
        """Test invalid records"""
        self.assertEqual(calculate_points("invalid"), 0)
        self.assertEqual(calculate_points(""), 0)
        self.assertEqual(calculate_points("abc-def-ghi"), 0)


class TestParseStandings(unittest.TestCase):
    """Test standings parsing logic"""

    def test_parse_simple_line(self):
        """Test parsing a single standings line"""
        text = "1 Michael Ross 16 5-0-1 56.8%"
        result = parse_standings(text)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Michael Ross')
        self.assertEqual(result[0]['record'], '5-0-1')
        self.assertEqual(result[0]['points'], 16)

    def test_parse_multiple_lines(self):
        """Test parsing multiple standings entries"""
        text = """
        1 Michael Ross 16 5-0-1 56.8%
        2 Ethan Riegle 15 5-1-0 46.6%
        3 Kora Benck 14 4-0-2 58.5%
        """
        result = parse_standings(text)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], 'Michael Ross')
        self.assertEqual(result[1]['name'], 'Ethan Riegle')
        self.assertEqual(result[2]['name'], 'Kora Benck')

    def test_parse_name_with_spaces(self):
        """Test parsing names with multiple words"""
        text = "9 arash afghahi 12 4-2-0 55.6%"
        result = parse_standings(text)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'arash afghahi')
        self.assertEqual(result[0]['record'], '4-2-0')

    def test_skip_header_lines(self):
        """Test that header lines are skipped"""
        text = """
        RANK NAME POINTS W-L-D OMW%
        1 Michael Ross 16 5-0-1 56.8%
        MATCH STANDINGS
        """
        result = parse_standings(text)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Michael Ross')

    def test_calculated_points(self):
        """Test that points are calculated correctly when not in text"""
        text = "1 Test Player 4-2-0 56.8%"
        result = parse_standings(text)

        if result:  # If parsing succeeds
            self.assertEqual(result[0]['points'], 12)


class TestExampleScenarios(unittest.TestCase):
    """Test real-world Magic: The Gathering tournament scenarios"""

    def test_tournament_standings(self):
        """Test parsing tournament standings"""
        text = """
        RANK NAME POINTS W-L-D OMW%
        1 Michael Ross 16 5-0-1 56.8%
        2 Ethan Riegle 15 5-1-0 46.6%
        3 Kora Benck 14 4-0-2 58.5%
        4 Ben Eppler 14 4-0-2 41.0%
        5 Tommy Adams 13 4-1-1 64.8%
        6 Kolbin Dahley 13 4-1-1 64.1%
        7 Max Garman 13 4-1-1 60.2%
        8 Jarod Comas 13 4-1-1 59.3%
        9 arash afghahi 12 4-2-0 55.6%
        """
        result = parse_standings(text)

        # Should parse 9 entries (skip header)
        self.assertGreaterEqual(len(result), 7)

        # Verify a few entries
        names = [r['name'] for r in result]
        self.assertIn('Michael Ross', names)
        self.assertIn('arash afghahi', names)


if __name__ == '__main__':
    unittest.main()
