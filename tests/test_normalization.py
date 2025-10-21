"""
Tests for normalization utilities.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils.normalization import normalize_text, parse_boolean, safe_int, safe_float


class TestNormalizeText:
    """Test cases for normalize_text function."""

    def test_basic_normalization(self):
        """Test basic text normalization."""
        assert normalize_text("Toyota") == "toyota"
        assert normalize_text("  Honda  ") == "honda"
        assert normalize_text("FORD") == "ford"

    def test_accent_removal(self):
        """Test accent removal."""
        assert normalize_text("camión") == "camion"
        assert normalize_text("niño") == "nino"
        assert normalize_text("corazón") == "corazon"

    def test_none_and_empty(self):
        """Test handling of None and empty values."""
        assert normalize_text(None) == ""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""

    def test_mixed_case_and_accents(self):
        """Test mixed case with accents."""
        assert normalize_text("CamIÓN") == "camion"
        assert normalize_text("NiÑo") == "nino"


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


class TestSafeInt:
    """Test cases for safe_int function."""

    def test_valid_integers(self):
        """Test valid integer conversion."""
        assert safe_int("123") == 123
        assert safe_int(456) == 456
        assert safe_int("1,234") == 1234
        assert safe_int("1 234") == 1234

    def test_invalid_input(self):
        """Test invalid input handling."""
        assert safe_int("abc") == 0
        assert safe_int(None) == 0
        assert safe_int("") == 0
        assert safe_int("12.34") == 12

    def test_default_value(self):
        """Test custom default value."""
        assert safe_int("abc", default=999) == 999
        assert safe_int(None, default=-1) == -1


class TestSafeFloat:
    """Test cases for safe_float function."""

    def test_valid_floats(self):
        """Test valid float conversion."""
        assert safe_float("123.45") == 123.45
        assert safe_float(456.78) == 456.78
        assert safe_float("1,234.56") == 1234.56
        assert safe_float("1 234.56") == 1234.56

    def test_invalid_input(self):
        """Test invalid input handling."""
        assert safe_float("abc") == 0.0
        assert safe_float(None) == 0.0
        assert safe_float("") == 0.0

    def test_default_value(self):
        """Test custom default value."""
        assert safe_float("abc", default=999.99) == 999.99
        assert safe_float(None, default=-1.0) == -1.0
