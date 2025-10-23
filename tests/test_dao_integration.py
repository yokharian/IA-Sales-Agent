"""
Test DAO integration in catalog_search.py
"""

import pytest
from unittest.mock import Mock, patch
from src.tools.catalog_search import catalog_search_impl
from src.db.vehicle_dao import get_makes, get_models, get_models_by_make, search_vehicles


class TestDAOIntegration:
    """Test DAO integration in catalog search."""

    @patch('src.tools.catalog_search.search_vehicles')
    @patch('src.tools.catalog_search.get_makes')
    def test_catalog_search_uses_dao_methods(self, mock_get_makes, mock_search_vehicles):
        """Test that catalog search uses DAO methods."""
        # Mock DAO responses
        mock_get_makes.return_value = ["Toyota", "Honda", "Ford"]
        
        mock_vehicle = Mock()
        mock_vehicle.stock_id = 1
        mock_vehicle.make = "Toyota"
        mock_vehicle.model = "Camry"
        mock_vehicle.year = 2020
        mock_vehicle.version = "LE"
        mock_vehicle.price = 25000.0
        mock_vehicle.km = 50000
        mock_vehicle.features = {}
        mock_search_vehicles.return_value = [mock_vehicle]
        
        preferences = {
            "make": "Toyota",
            "budget_max": 30000,
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Verify DAO methods were called
        mock_get_makes.assert_called_once_with(limit=1000)
        mock_search_vehicles.assert_called_once()
        
        # Verify results
        assert len(results) == 1
        assert results[0].make == "Toyota"

    @patch('src.tools.catalog_search.search_vehicles')
    @patch('src.tools.catalog_search.get_models_by_make')
    def test_catalog_search_with_model_filter(self, mock_get_models_by_make, mock_search_vehicles):
        """Test catalog search with model filtering using DAO."""
        # Mock DAO responses
        mock_get_models_by_make.return_value = ["Camry", "Corolla", "Prius"]
        
        mock_vehicle = Mock()
        mock_vehicle.stock_id = 1
        mock_vehicle.make = "Toyota"
        mock_vehicle.model = "Camry"
        mock_vehicle.year = 2020
        mock_vehicle.version = "LE"
        mock_vehicle.price = 25000.0
        mock_vehicle.km = 50000
        mock_vehicle.features = {}
        mock_search_vehicles.return_value = [mock_vehicle]
        
        preferences = {
            "make": "Toyota",
            "model": "Camry",
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Verify DAO methods were called
        mock_get_models_by_make.assert_called_once_with("Toyota", limit=1000)
        mock_search_vehicles.assert_called_once()
        
        # Verify results
        assert len(results) == 1
        assert results[0].model == "Camry"

    @patch('src.tools.catalog_search.search_vehicles')
    def test_catalog_search_price_filtering(self, mock_search_vehicles):
        """Test that price filtering is passed to DAO."""
        mock_vehicle = Mock()
        mock_vehicle.stock_id = 1
        mock_vehicle.make = "Toyota"
        mock_vehicle.model = "Camry"
        mock_vehicle.year = 2020
        mock_vehicle.version = "LE"
        mock_vehicle.price = 25000.0
        mock_vehicle.km = 50000
        mock_vehicle.features = {}
        mock_search_vehicles.return_value = [mock_vehicle]
        
        preferences = {
            "budget_min": 20000,
            "budget_max": 30000,
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Verify search_vehicles was called with price parameters
        call_args = mock_search_vehicles.call_args
        assert call_args[1]['min_price'] == 20000
        assert call_args[1]['max_price'] == 30000

    @patch('src.tools.catalog_search.search_vehicles')
    def test_catalog_search_km_filtering_post_processing(self, mock_search_vehicles):
        """Test that km filtering is applied after DAO query."""
        # Create vehicles with different km values
        vehicle1 = Mock()
        vehicle1.stock_id = 1
        vehicle1.make = "Toyota"
        vehicle1.model = "Camry"
        vehicle1.year = 2020
        vehicle1.version = "LE"
        vehicle1.price = 25000.0
        vehicle1.km = 30000  # Under limit
        vehicle1.features = {}
        
        vehicle2 = Mock()
        vehicle2.stock_id = 2
        vehicle2.make = "Honda"
        vehicle2.model = "Civic"
        vehicle2.year = 2020
        vehicle2.version = "LX"
        vehicle2.price = 22000.0
        vehicle2.km = 80000  # Over limit
        vehicle2.features = {}
        
        mock_search_vehicles.return_value = [vehicle1, vehicle2]
        
        preferences = {
            "km_max": 50000,
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Should only return vehicle1 (under km limit)
        assert len(results) == 1
        assert results[0].stock_id == 1
        assert results[0].km == 30000

    @patch('src.tools.catalog_search.search_vehicles')
    def test_catalog_search_features_filtering_post_processing(self, mock_search_vehicles):
        """Test that features filtering is applied after DAO query."""
        # Create vehicles with different features
        vehicle1 = Mock()
        vehicle1.stock_id = 1
        vehicle1.make = "Toyota"
        vehicle1.model = "Camry"
        vehicle1.year = 2020
        vehicle1.version = "LE"
        vehicle1.price = 25000.0
        vehicle1.km = 50000
        vehicle1.features = {"bluetooth": True, "air_play": True}
        
        vehicle2 = Mock()
        vehicle2.stock_id = 2
        vehicle2.make = "Honda"
        vehicle2.model = "Civic"
        vehicle2.year = 2020
        vehicle2.version = "LX"
        vehicle2.price = 22000.0
        vehicle2.km = 50000
        vehicle2.features = {"bluetooth": True, "air_play": False}  # Missing air_play
        
        mock_search_vehicles.return_value = [vehicle1, vehicle2]
        
        preferences = {
            "features": ["bluetooth", "air_play"],
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Should only return vehicle1 (has all required features)
        assert len(results) == 1
        assert results[0].stock_id == 1
        assert results[0].features["bluetooth"] is True
        assert results[0].features["air_play"] is True

    @patch('src.tools.catalog_search.search_vehicles')
    def test_catalog_search_sorting(self, mock_search_vehicles):
        """Test that sorting is applied after DAO query."""
        # Create vehicles with different prices
        vehicle1 = Mock()
        vehicle1.stock_id = 1
        vehicle1.make = "Toyota"
        vehicle1.model = "Camry"
        vehicle1.year = 2020
        vehicle1.version = "LE"
        vehicle1.price = 30000.0  # Higher price
        vehicle1.km = 50000
        vehicle1.features = {}
        
        vehicle2 = Mock()
        vehicle2.stock_id = 2
        vehicle2.make = "Honda"
        vehicle2.model = "Civic"
        vehicle2.year = 2020
        vehicle2.version = "LX"
        vehicle2.price = 20000.0  # Lower price
        vehicle2.km = 50000
        vehicle2.features = {}
        
        mock_search_vehicles.return_value = [vehicle1, vehicle2]
        
        preferences = {
            "sort_by": "price_low",
            "max_results": 5
        }
        
        results = catalog_search_impl(preferences)
        
        # Should be sorted by price (low to high)
        assert len(results) == 2
        assert results[0].price == 20000.0  # Honda first (lower price)
        assert results[1].price == 30000.0  # Toyota second (higher price)
