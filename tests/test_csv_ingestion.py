"""
Tests for CSV ingestion functionality.
"""

import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from scripts.ingest_csv import process_vehicle_row, parse_boolean


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


class TestCSVIngestion:
    """Test cases for CSV ingestion functionality."""

    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV data for testing."""
        return {
            "stock_id": [1001, 1002, 1003],
            "make": ["Toyota", "Honda", "Ford"],
            "model": ["Corolla", "Civic", "Focus"],
            "year": [2020, 2019, 2021],
            "version": ["LE", "LX", "SE"],
            "km": [25000, 32000, 18000],
            "price": [18500.00, 16800.00, 19500.00],
            "bluetooth": ["Sí", "Sí", "No"],
            "car_play": ["Sí", "No", "Sí"],
            "largo": [4.6, 4.5, 4.4],
            "ancho": [1.8, 1.8, 1.8],
            "altura": [1.5, 1.5, 1.4],
        }

    def test_process_vehicle_row(self, sample_csv_data):
        """Test processing a single CSV row."""
        df = pd.DataFrame(sample_csv_data)
        row = df.iloc[0]

        result = process_vehicle_row(row)

        assert result["stock_id"] == 1001
        assert result["make"] == "toyota"
        assert result["model"] == "corolla"
        assert result["year"] == 2020
        assert result["version"] == "le"
        assert result["km"] == 25000
        assert result["price"] == 18500.00
        assert result["features"]["bluetooth"] == True
        assert result["features"]["car_play"] == True
        assert result["largo"] == 4.6
        assert result["ancho"] == 1.8
        assert result["altura"] == 1.5

    def test_process_vehicle_row_with_missing_data(self):
        """Test processing row with missing optional data."""
        row_data = {
            "stock_id": 1004,
            "make": "Chevrolet",
            "model": "Cruze",
            "year": 2018,
            "km": 45000,
            "price": 14200.00,
            "bluetooth": "No",
        }

        row = pd.Series(row_data)
        result = process_vehicle_row(row)

        assert result["stock_id"] == 1004
        assert result["make"] == "chevrolet"
        assert result["model"] == "cruze"
        assert result["version"] is None
        assert result["features"]["bluetooth"] == False
        assert result["largo"] is None
        assert result["ancho"] is None
        assert result["altura"] is None

    def test_process_vehicle_row_with_invalid_data(self):
        """Test processing row with invalid data."""
        row_data = {
            "stock_id": "invalid",
            "make": "Toyota",
            "model": "Corolla",
            "year": "not_a_year",
            "km": "not_a_number",
            "price": "not_a_price",
            "bluetooth": "Sí",
        }

        row = pd.Series(row_data)

        # Should handle invalid data gracefully with Pydantic validation
        result = process_vehicle_row(row)

        assert result["stock_id"] is None  # Invalid data returns None
        assert result["year"] is None  # Invalid data returns None
        assert result["km"] is None  # Invalid data returns None
        assert result["price"] is None  # Invalid data returns None
        assert result["features"]["bluetooth"] == True

    def test_create_sample_csv_file(self):
        """Test creating a sample CSV file for testing."""
        sample_data = {
            "stock_id": [1001, 1002],
            "make": ["Toyota", "Honda"],
            "model": ["Corolla", "Civic"],
            "year": [2020, 2019],
            "km": [25000, 32000],
            "price": [18500.00, 16800.00],
            "bluetooth": ["Sí", "No"],
            "car_play": ["Sí", "Sí"],
            "largo": [4.6, 4.5],
            "ancho": [1.8, 1.8],
            "altura": [1.5, 1.5],
        }

        df = pd.DataFrame(sample_data)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df.to_csv(f.name, index=False)

            # Verify CSV was created correctly
            loaded_df = pd.read_csv(f.name)
            assert len(loaded_df) == 2
            assert loaded_df["stock_id"].iloc[0] == 1001
            assert loaded_df["make"].iloc[0] == "Toyota"

            # Clean up
            Path(f.name).unlink()
