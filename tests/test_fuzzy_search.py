"""
Test fuzzy search functionality in catalog_search.py
"""

import pytest
from unittest.mock import Mock, patch
from src.tools.catalog_search import _fuzzy_search_make, _fuzzy_search_model, catalog_search_impl
from src.db.vehicle_dao import get_makes, get_models, get_models_by_make, search_vehicles


class TestFuzzySearch:
    """Test fuzzy search functionality."""

    @patch('src.tools.catalog_search.get_makes')
    def test_fuzzy_search_make_exact_match(self, mock_get_makes):
        """Test fuzzy search with exact match."""
        # Mock DAO response
        mock_get_makes.return_value = ["Toyota", "Honda", "Ford", "BMW"]
        
        result = _fuzzy_search_make("Toyota")
        assert result == "Toyota"

    @patch('src.tools.catalog_search.get_makes')
    def test_fuzzy_search_make_fuzzy_match(self, mock_get_makes):
        """Test fuzzy search with fuzzy match."""
        # Mock DAO response
        mock_get_makes.return_value = ["Toyota", "Honda", "Ford", "BMW"]
        
        result = _fuzzy_search_make("Toyta")  # Typo in Toyota
        assert result == "Toyota"

    @patch('src.tools.catalog_search.get_makes')
    def test_fuzzy_search_make_no_match(self, mock_get_makes):
        """Test fuzzy search with no good match."""
        # Mock DAO response
        mock_get_makes.return_value = ["Toyota", "Honda", "Ford", "BMW"]
        
        result = _fuzzy_search_make("Xyz")  # No match
        assert result is None

    @patch('src.tools.catalog_search.get_models_by_make')
    def test_fuzzy_search_model_with_make(self, mock_get_models_by_make):
        """Test fuzzy search for model with make filter."""
        # Mock DAO response
        mock_get_models_by_make.return_value = ["Camry", "Corolla", "Prius", "RAV4"]
        
        result = _fuzzy_search_model("Camry", make="Toyota")
        assert result == "Camry"

    @patch('src.tools.catalog_search.get_models_by_make')
    def test_fuzzy_search_model_fuzzy_match(self, mock_get_models_by_make):
        """Test fuzzy search for model with fuzzy match."""
        # Mock DAO response
        mock_get_models_by_make.return_value = ["Camry", "Corolla", "Prius", "RAV4"]
        
        result = _fuzzy_search_model("Camri", make="Toyota")  # Typo in Camry
        assert result == "Camry"

    @patch('src.tools.catalog_search.search_vehicles')
    @patch('src.tools.catalog_search.get_makes')
    def test_catalog_search_with_fuzzy_make(self, mock_get_makes, mock_search_vehicles):
        """Test catalog search with fuzzy make matching."""
        # Mock DAO response for fuzzy search
        mock_get_makes.return_value = ["Toyota", "Honda", "Ford", "BMW"]
        
        # Mock vehicle data
        mock_vehicle = Mock()
        mock_vehicle.stock_id = 1
        mock_vehicle.make = "Toyota"
        mock_vehicle.model = "Camry"
        mock_vehicle.year = 2020
        mock_vehicle.version = "LE"
        mock_vehicle.price = 25000.0
        mock_vehicle.km = 50000
        mock_vehicle.features = {"bluetooth": True}
        
        # Mock the DAO search_vehicles method
        mock_search_vehicles.return_value = [mock_vehicle]
        
        preferences = {
            "make": "Toyta",  # Typo in Toyota
            "budget_max": 30000,
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Should find Toyota despite the typo
        assert len(results) == 1
        assert results[0].make == "Toyota"
        assert results[0].model == "Camry"

    @patch('src.tools.catalog_search.get_makes')
    def test_catalog_search_no_fuzzy_match(self, mock_get_makes):
        """Test catalog search when no fuzzy match is found."""
        # Mock DAO response for fuzzy search
        mock_get_makes.return_value = ["Toyota", "Honda", "Ford", "BMW"]
        
        preferences = {
            "make": "Xyz",  # No match
            "budget_max": 30000,
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Should return empty results
        assert len(results) == 0
