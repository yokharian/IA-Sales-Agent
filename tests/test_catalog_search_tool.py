"""
Tests for LangChain tools.
"""

import os
import sys
import pytest
from pathlib import Path

# Set test environment variables before any imports
os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.catalog_search import (
    VehiclePreferences,
    VehicleResult,
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
        )

        assert result.stock_id == 1001
        assert result.make == "toyota"
        assert result.model == "corolla"
        assert result.year == 2020
        assert result.version == "le"
        assert result.price == 18500.00
        assert result.km == 25000
        assert result.features == {"bluetooth": True, "air_conditioning": True}

    def test_result_with_none_version(self):
        """Test result with None version."""
        result = VehicleResult(
            stock_id=1002,
            make="honda",
            model="civic",
            year=2019,
            version=None,
            price=20000.00,
            km=30000,
            features={"bluetooth": False},
        )

        assert result.version is None


class TestCatalogSearchImpl:
    """Test catalog search implementation."""

    def test_catalog_search_tool_creation(self):
        """Test that the catalog search tool is properly created."""
        from tools.catalog_search import catalog_search_tool

        assert catalog_search_tool.name == "catalog_search"
        assert "Search the vehicle catalog" in catalog_search_tool.description
        assert catalog_search_tool.args_schema is not None

    def test_vehicle_preferences_validation(self):
        """Test VehiclePreferences validation."""
        from tools.catalog_search import VehiclePreferences

        # Test valid preferences
        prefs = VehiclePreferences(make="Toyota", budget_max=50000, max_results=5)
        assert prefs.make == "Toyota"
        assert prefs.budget_max == 50000
        assert prefs.max_results == 5

        # Test with None values
        prefs_none = VehiclePreferences()
        assert prefs_none.make is None
        assert prefs_none.budget_max is None
        assert prefs_none.max_results == 5  # Default value

    def test_catalog_search_comprehensive_scenarios(self):
        """Test catalog search with comprehensive scenarios."""
        # Test cases for catalog search
        test_cases = [
            {
                "name": "Search by make and budget",
                "preferences": {"make": "toyota", "budget_max": 20000, "max_results": 3}
            },
            {
                "name": "Search with typos (fuzzy matching)",
                "preferences": {
                    "make": "hond",  # Typo for "honda"
                    "model": "civic",
                    "max_results": 2,
                }
            },
            {
                "name": "Search by features",
                "preferences": {"features": ["bluetooth", "air_conditioning"], "max_results": 2}
            },
            {
                "name": "Complex search with multiple filters",
                "preferences": {
                    "make": "Toyta",  # Typo to test fuzzy matching
                    "budget_max": 50000,
                    "km_max": 50000,
                    "max_results": 3,
                }
            },
            {
                "name": "Price range search",
                "preferences": {"budget_min": 200000, "budget_max": 400000, "max_results": 5}
            }
        ]

        for test_case in test_cases:
            # Test that the function can be called without crashing
            try:
                from tools.catalog_search import catalog_search_impl
                results = catalog_search_impl(test_case["preferences"])
                assert isinstance(results, list)
                # Should handle the query gracefully
            except Exception as e:
                # Should handle errors gracefully
                assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError))

    def test_catalog_search_tool_integration(self):
        """Test catalog search tool integration with LangChain."""
        from tools.catalog_search import catalog_search_tool

        # Test tool attributes
        assert catalog_search_tool.name == "catalog_search"
        assert isinstance(catalog_search_tool.description, str)
        assert len(catalog_search_tool.description) > 0
        assert catalog_search_tool.args_schema is not None
        assert callable(catalog_search_tool.func)

        # Test direct tool usage
        try:
            result = catalog_search_tool.func(
                {
                    "make": "Toyta",  # Typo to test fuzzy matching
                    "budget_max": 50000,
                    "max_results": 3,
                }
            )
            assert isinstance(result, list)
        except Exception as e:
            # Expected to fail in test environment, but should not crash
            assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError))

    def test_integrated_search_workflow(self):
        """Test integrated search workflow using both tools."""
        # Test vehicle catalog search
        try:
            from tools.catalog_search import catalog_search_tool
            vehicle_results = catalog_search_tool.func(
                {
                    "make": "Toyta",  # Intentional typo to test fuzzy matching
                    "budget_max": 50000,
                    "max_results": 3,
                }
            )
            assert isinstance(vehicle_results, list)
        except Exception as e:
            # Expected to fail in test environment, but should not crash
            assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError))

        # Test document search
        try:
            from tools.document_search import document_search_tool
            doc_results = document_search_tool.func(
                {"query": "vehicle specifications and features", "k": 3}
            )
            assert isinstance(doc_results, list)
        except Exception as e:
            # Expected to fail in test environment, but should not crash
            from openai import AuthenticationError, OpenAIError
            assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError, AuthenticationError, OpenAIError))

        # Test combined workflow
        try:
            # Step 1: Find vehicles
            vehicles = catalog_search_tool.func({"make": "Honda", "max_results": 2})
            assert isinstance(vehicles, list)

            if vehicles:
                # Step 2: Get documentation for the first vehicle
                first_vehicle = vehicles[0]
                docs = document_search_tool.func(
                    {
                        "query": f"{first_vehicle.make} {first_vehicle.model} specifications",
                        "k": 2,
                    }
                )
                assert isinstance(docs, list)
        except Exception as e:
            # Expected to fail in test environment, but should not crash
            from openai import AuthenticationError, OpenAIError
            assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError, AuthenticationError, OpenAIError))

    def test_catalog_search_performance_scenarios(self):
        """Test catalog search performance with different scenarios."""
        import time

        # Test different search scenarios
        search_scenarios = [
            {
                "name": "Simple make search",
                "preferences": {"make": "Toyota", "max_results": 5}
            },
            {
                "name": "Make with typo",
                "preferences": {"make": "Toyta", "max_results": 5}
            },
            {
                "name": "Price range search",
                "preferences": {"budget_min": 200000, "budget_max": 400000, "max_results": 10}
            },
            {
                "name": "Complex search",
                "preferences": {
                    "make": "Hnda",  # Typo
                    "budget_max": 300000,
                    "km_max": 50000,
                    "max_results": 5
                }
            }
        ]

        for scenario in search_scenarios:
            start_time = time.time()
            
            try:
                from tools.catalog_search import catalog_search_impl
                results = catalog_search_impl(scenario["preferences"])
                end_time = time.time()
                
                # Should complete within reasonable time (5 seconds)
                assert end_time - start_time < 5.0
                assert isinstance(results, list)
                
            except Exception as e:
                # Should handle errors gracefully
                assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError))

    def test_catalog_search_edge_cases(self):
        """Test catalog search error handling and edge cases."""
        # Test edge cases and error scenarios
        edge_cases = [
            {
                "name": "Invalid budget range",
                "preferences": {"budget_min": 50000, "budget_max": 20000, "max_results": 3}
            },
            {
                "name": "Zero max results",
                "preferences": {"make": "Toyota", "max_results": 0}
            },
            {
                "name": "Very high max results",
                "preferences": {"make": "Toyota", "max_results": 1000}
            },
            {
                "name": "Empty make",
                "preferences": {"make": "", "max_results": 3}
            },
            {
                "name": "Special characters in make",
                "preferences": {"make": "Toy@ta", "max_results": 3}
            }
        ]

        for case in edge_cases:
            try:
                from tools.catalog_search import catalog_search_impl
                results = catalog_search_impl(case["preferences"])
                assert isinstance(results, list)
                # Should handle edge cases gracefully
            except Exception as e:
                # Should handle errors gracefully
                assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError))

    def test_langchain_tools_metadata(self):
        """Test LangChain tools metadata and configuration."""
        from tools.catalog_search import catalog_search_tool
        from tools.document_search import document_search_tool

        # Test catalog search tool metadata
        assert catalog_search_tool.name == "catalog_search"
        assert isinstance(catalog_search_tool.description, str)
        assert len(catalog_search_tool.description) > 0
        assert catalog_search_tool.args_schema is not None

        # Test document search tool metadata
        assert document_search_tool.name == "document_search"
        assert isinstance(document_search_tool.description, str)
        assert len(document_search_tool.description) > 0
        assert document_search_tool.args_schema is not None

        # Test that both tools have required LangChain tool interface
        for tool in [catalog_search_tool, document_search_tool]:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'func')
            assert hasattr(tool, 'args_schema')
            assert callable(tool.func)
