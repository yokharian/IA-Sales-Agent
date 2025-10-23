"""
Tests for LangChain tools.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.catalog_search import (
    VehiclePreferences,
    VehicleResult,
    catalog_search_impl,
)


class TestVehiclePreferences:
    """Test VehiclePreferences schema."""

    def test_valid_preferences(self):
        """Test valid preference creation."""
        prefs = VehiclePreferences(
            budget_min=10000,
            budget_max=25000,
            make="toyota",
            model="corolla",
            km_max=50000,
            features=["bluetooth", "air_conditioning"],
        )

        assert prefs.budget_min == 10000
        assert prefs.budget_max == 25000
        assert prefs.make == "toyota"
        assert prefs.model == "corolla"
        assert prefs.km_max == 50000
        assert prefs.features == ["bluetooth", "air_conditioning"]
        assert prefs.sort_by == "relevance"
        assert prefs.max_results == 5

    def test_minimal_preferences(self):
        """Test minimal preference creation."""
        prefs = VehiclePreferences()

        assert prefs.budget_min is None
        assert prefs.budget_max is None
        assert prefs.make is None
        assert prefs.model is None
        assert prefs.km_max is None
        assert prefs.features is None
        assert prefs.sort_by == "relevance"
        assert prefs.max_results == 5

    def test_invalid_budget(self):
        """Test invalid budget validation."""
        with pytest.raises(ValueError):
            VehiclePreferences(budget_min=-1000)

        with pytest.raises(ValueError):
            VehiclePreferences(budget_max=-5000)

    def test_invalid_max_results(self):
        """Test invalid max_results validation."""
        with pytest.raises(ValueError):
            VehiclePreferences(max_results=0)

        with pytest.raises(ValueError):
            VehiclePreferences(max_results=25)


class TestVehicleResult:
    """Test VehicleResult schema."""

    def test_valid_result(self):
        """Test valid result creation."""
        result = VehicleResult(
            stock_id=1001,
            make="toyota",
            model="corolla",
            year=2020,
            version="le",
            price=18500.00,
            km=25000,
            features={"bluetooth": True, "air_conditioning": True},
            similarity_score=0.95,
        )

        assert result.stock_id == 1001
        assert result.make == "toyota"
        assert result.model == "corolla"
        assert result.year == 2020
        assert result.version == "le"
        assert result.price == 18500.00
        assert result.km == 25000
        assert result.features == {"bluetooth": True, "air_conditioning": True}
        assert result.similarity_score == 0.95

    def test_invalid_similarity_score(self):
        """Test invalid similarity score validation."""
        with pytest.raises(ValueError):
            VehicleResult(
                stock_id=1001,
                make="toyota",
                model="corolla",
                year=2020,
                price=18500.00,
                km=25000,
                features={},
                similarity_score=1.5,  # Invalid: > 1
            )


class TestCatalogSearchImpl:
    """Test catalog search implementation."""

    @patch("tools.catalog_search.VehicleSearchService")
    @patch("tools.catalog_search.get_session_sync")
    def test_search_with_filters(self, mock_session, mock_search_service):
        """Test search with filters."""
        from db.models import Vehicle

        # Mock database session
        mock_vehicle = Vehicle(
            stock_id=1001,
            make="toyota",
            model="corolla",
            year=2020,
            price=18500.00,
            km=25000,
            features={"bluetooth": True},
        )

        mock_session.return_value.__enter__.return_value.exec.return_value = [
            mock_vehicle
        ]

        # Mock search service
        mock_search_service.return_value.search_vehicles.return_value = [
            {"stock_id": 1001, "relevance_score": 0.9}
        ]

        preferences = {"budget_min": 15000, "budget_max": 20000, "make": "toyota"}

        results = catalog_search_impl(preferences)

        assert len(results) == 1
        assert results[0].stock_id == 1001
        assert results[0].make == "toyota"
        assert results[0].similarity_score == 0.9
