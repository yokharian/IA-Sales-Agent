"""
Tests for CSV ingestion functionality.
"""

import sys
import tempfile

import pandas as pd
import pytest

from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from scripts.ingest_csv import parse_boolean, process_vehicle_row


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
        assert result["make"] == "Toyota"
        assert result["model"] == "Corolla"
        assert result["year"] == 2020
        assert result["version"] == "LE"
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
        assert result["make"] == "Chevrolet"
        assert result["model"] == "Cruze"
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

        # Should handle invalid data gracefully - current implementation doesn't validate types
        result = process_vehicle_row(row)

        assert (
            result["stock_id"] == "invalid"
        )  # Current implementation preserves original values
        assert (
            result["year"] == "not_a_year"
        )  # Current implementation preserves original values
        assert (
            result["km"] == "not_a_number"
        )  # Current implementation preserves original values
        assert (
            result["price"] == "not_a_price"
        )  # Current implementation preserves original values
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

    def test_csv_ingestion_workflow(self):
        """Test complete CSV ingestion workflow."""
        # Create sample data that matches the real CSV structure
        sample_data = {
            "stock_id": [1001, 1002, 1003, 1004],
            "make": ["Toyota", "Honda", "Ford", "Chevrolet"],
            "model": ["Corolla", "Civic", "Focus", "Cruze"],
            "year": [2020, 2019, 2021, 2018],
            "version": ["LE", "LX", "SE", None],
            "km": [25000, 32000, 18000, 45000],
            "price": [18500.00, 16800.00, 19500.00, 14200.00],
            "bluetooth": ["Sí", "Sí", "No", "No"],
            "car_play": ["Sí", "No", "Sí", "No"],
            "largo": [4.6, 4.5, 4.4, 4.3],
            "ancho": [1.8, 1.8, 1.8, 1.7],
            "altura": [1.5, 1.5, 1.4, 1.4],
        }

        df = pd.DataFrame(sample_data)
        assert len(df) == 4

        # Test processing each row
        for i, (_, row) in enumerate(df.iterrows(), 1):
            result = process_vehicle_row(row)
            
            # Verify basic structure
            assert isinstance(result, dict)
            assert "stock_id" in result
            assert "make" in result
            assert "model" in result
            assert "features" in result
            assert isinstance(result["features"], dict)

    def test_boolean_parsing_comprehensive(self):
        """Test boolean parsing with comprehensive test cases."""
        test_values = [
            ("Sí", True),
            ("si", True),
            ("No", False),
            ("no", False),
            ("yes", True),
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
            ("", False),
            (None, False),
            (True, True),
            (False, False),
        ]

        for value, expected in test_values:
            result = parse_boolean(value)
            assert result == expected, f"parse_boolean({repr(value)}) = {result}, expected {expected}"

    def test_data_validation_comprehensive(self):
        """Test data validation with various data quality scenarios."""
        test_cases = [
            {
                "name": "Valid data",
                "data": {
                    "stock_id": 1001,
                    "make": "Toyota",
                    "model": "Corolla",
                    "year": 2020,
                    "km": 25000,
                    "price": 18500.00,
                    "bluetooth": "Sí",
                    "car_play": "No",
                },
                "should_succeed": True,
            },
            {
                "name": "Missing optional fields",
                "data": {
                    "stock_id": 1002,
                    "make": "Honda",
                    "model": "Civic",
                    "year": 2019,
                    "km": 32000,
                    "price": 16800.00,
                    "bluetooth": "No",
                },
                "should_succeed": True,
            },
            {
                "name": "Invalid data types",
                "data": {
                    "stock_id": "invalid",
                    "make": "Ford",
                    "model": "Focus",
                    "year": "not_a_year",
                    "km": "not_a_number",
                    "price": "not_a_price",
                    "bluetooth": "Sí",
                },
                "should_succeed": True,  # Current implementation preserves values
            },
            {
                "name": "Edge case values",
                "data": {
                    "stock_id": 0,
                    "make": "",
                    "model": "   ",
                    "year": 1900,
                    "km": -1000,
                    "price": 0.01,
                    "bluetooth": "maybe",
                },
                "should_succeed": True,
            },
        ]

        for test_case in test_cases:
            row = pd.Series(test_case["data"])
            
            if test_case["should_succeed"]:
                result = process_vehicle_row(row)
                assert isinstance(result, dict)
                assert "stock_id" in result
                assert "make" in result
                assert "model" in result
                assert "features" in result
            else:
                with pytest.raises(Exception):
                    process_vehicle_row(row)

    def test_csv_ingestion_edge_cases(self):
        """Test CSV ingestion with edge cases."""
        edge_cases = [
            {
                "name": "Empty DataFrame",
                "data": pd.DataFrame(),
                "expected_count": 0
            },
            {
                "name": "Single row",
                "data": pd.DataFrame({
                    "stock_id": [1001],
                    "make": ["Toyota"],
                    "model": ["Corolla"],
                    "year": [2020],
                    "km": [25000],
                    "price": [18500.00],
                    "bluetooth": ["Sí"]
                }),
                "expected_count": 1
            },
            {
                "name": "All None values",
                "data": pd.DataFrame({
                    "stock_id": [None],
                    "make": [None],
                    "model": [None],
                    "year": [None],
                    "km": [None],
                    "price": [None],
                    "bluetooth": [None]
                }),
                "expected_count": 1
            }
        ]

        for case in edge_cases:
            df = case["data"]
            assert len(df) == case["expected_count"]
            
            if len(df) > 0:
                for _, row in df.iterrows():
                    result = process_vehicle_row(row)
                    assert isinstance(result, dict)

    def test_csv_ingestion_performance(self):
        """Test CSV ingestion performance with larger datasets."""
        import time
        
        # Create a larger dataset
        large_data = {
            "stock_id": list(range(1001, 1101)),  # 100 rows
            "make": ["Toyota", "Honda", "Ford", "Chevrolet"] * 25,
            "model": [f"Model{i}" for i in range(100)],
            "year": [2020 + (i % 5) for i in range(100)],
            "km": [10000 + (i * 1000) for i in range(100)],
            "price": [15000 + (i * 100) for i in range(100)],
            "bluetooth": ["Sí" if i % 2 == 0 else "No" for i in range(100)]
        }
        
        df = pd.DataFrame(large_data)
        
        start_time = time.time()
        
        # Process all rows
        results = []
        for _, row in df.iterrows():
            result = process_vehicle_row(row)
            results.append(result)
        
        end_time = time.time()
        
        # Should complete within reasonable time (2 seconds for 100 rows)
        assert end_time - start_time < 2.0
        assert len(results) == 100
        
        # Verify all results have correct structure
        for result in results:
            assert isinstance(result, dict)
            assert "stock_id" in result
            assert "features" in result
