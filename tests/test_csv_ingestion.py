"""
Tests for CSV ingestion functionality.
"""

import pytest
import sys
import tempfile
import pandas as pd
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from db.models import Vehicle
from scripts.ingest_csv import process_vehicle_row


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
            "air_conditioning": ["Sí", "Sí", "Sí"],
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
        assert result["features"]["air_conditioning"] == True

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
        assert result["dims"] is None

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

        # Should handle invalid data gracefully
        result = process_vehicle_row(row)

        assert result["stock_id"] == 0  # Default value
        assert result["year"] == 0  # Default value
        assert result["km"] == 0  # Default value
        assert result["price"] == 0.0  # Default value
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
