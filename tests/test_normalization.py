"""
Tests for normalization utilities.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.normalization import parse_boolean


class TestParseBoolean:
    """Test cases for parse_boolean function."""

    def test_truthy_values(self):
        """Test truthy string values."""
        assert parse_boolean("Sí") == True
        assert parse_boolean("si") == True
        assert parse_boolean("yes") == True
        assert parse_boolean("true") == True
        assert parse_boolean("1") == True
        assert parse_boolean("verdadero") == True
        assert parse_boolean("v") == True

    def test_falsy_values(self):
        """Test falsy string values."""
        assert parse_boolean("No") == False
        assert parse_boolean("no") == False
        assert parse_boolean("false") == False
        assert parse_boolean("0") == False
        assert parse_boolean("") == False
        assert parse_boolean("   ") == False

    def test_boolean_input(self):
        """Test boolean input."""
        assert parse_boolean(True) == True
        assert parse_boolean(False) == False

    def test_none_input(self):
        """Test None input."""
        assert parse_boolean(None) == False
