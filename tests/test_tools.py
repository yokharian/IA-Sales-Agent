"""
Tests for LangChain tools.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.catalog_search import (
    VehiclePreferences,
    VehicleResult,
    catalog_search_impl,
    catalog_search_tool,
)
from tools.finance_calculation import (
    FinanceCalculationInput,
    FinanceCalculationResult,
    finance_calculation_impl,
    finance_calculation_tool,
    calculate_monthly_payment,
)
from tools.registry import get_tool, get_all_tools, get_tool_names


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
        from models.vehicle import Vehicle

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


class TestFinanceCalculationInput:
    """Test FinanceCalculationInput schema."""

    def test_valid_input(self):
        """Test valid input creation."""
        calc_input = FinanceCalculationInput(
            price=25000, down_payment=5000, term_years=5, interest_rate=5.5
        )

        assert calc_input.price == 25000
        assert calc_input.down_payment == 5000
        assert calc_input.term_years == 5
        assert calc_input.interest_rate == 5.5
        assert calc_input.include_amortization is False

    def test_invalid_price(self):
        """Test invalid price validation."""
        with pytest.raises(ValueError):
            FinanceCalculationInput(price=0, down_payment=1000, term_years=5)

    def test_invalid_term(self):
        """Test invalid term validation."""
        with pytest.raises(ValueError):
            FinanceCalculationInput(price=25000, down_payment=1000, term_years=0)


class TestCalculateMonthlyPayment:
    """Test monthly payment calculation."""

    def test_standard_loan(self):
        """Test standard loan calculation."""
        payment = calculate_monthly_payment(20000, 0.055, 5)
        expected = 381.32  # Approximate
        assert abs(payment - expected) < 1.0

    def test_zero_interest(self):
        """Test zero interest loan."""
        payment = calculate_monthly_payment(20000, 0.0, 5)
        expected = 20000 / (5 * 12)  # 333.33
        assert abs(payment - expected) < 0.01


class TestFinanceCalculationImpl:
    """Test finance calculation implementation."""

    def test_standard_calculation(self):
        """Test standard finance calculation."""
        inputs = {
            "price": 25000,
            "down_payment": 5000,
            "term_years": 5,
            "interest_rate": 5.5,
        }

        result = finance_calculation_impl(inputs)

        assert isinstance(result, FinanceCalculationResult)
        assert result.payment_breakdown.principal_amount == 20000
        assert result.payment_breakdown.monthly_payment > 0
        assert result.payment_breakdown.total_interest > 0
        assert len(result.recommendations) > 0

    def test_full_down_payment(self):
        """Test when down payment covers full price."""
        inputs = {"price": 25000, "down_payment": 25000, "term_years": 5}

        result = finance_calculation_impl(inputs)

        assert result.payment_breakdown.monthly_payment == 0
        assert result.payment_breakdown.principal_amount == 0
        assert "no financing needed" in result.recommendations[0].lower()


class TestToolRegistry:
    """Test tool registry functionality."""

    def test_get_all_tools(self):
        """Test getting all tools."""
        tools = get_all_tools()

        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "catalog_search" in tool_names
        assert "finance_calculation" in tool_names
        assert "fact_check" in tool_names

    def test_get_tool_names(self):
        """Test getting tool names."""
        names = get_tool_names()

        assert "catalog_search" in names
        assert "finance_calculation" in names
        assert "fact_check" in names

    def test_get_tool(self):
        """Test getting specific tool."""
        tool = get_tool("catalog_search")

        assert tool.name == "catalog_search"
        assert tool.func is not None
        assert tool.description is not None

    def test_get_nonexistent_tool(self):
        """Test getting nonexistent tool."""
        with pytest.raises(KeyError):
            get_tool("nonexistent_tool")
