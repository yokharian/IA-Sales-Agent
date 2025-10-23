#!/usr/bin/env python3
"""
Demo script for LangChain tools.

This script demonstrates the functionality of all the LangChain tools
for vehicle search and recommendations.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.registry import get_all_tools
from tools.catalog_search import catalog_search_impl
from tools.finance_calculation import finance_calculation_impl


def demo_catalog_search():
    """Demonstrate catalog search tool."""
    print("🔍 Catalog Search Tool Demo")
    print("=" * 50)

    # Test 1: Search by make and budget
    print("\n1. Searching for Toyota vehicles under $20,000:")
    preferences = {"make": "toyota", "budget_max": 20000, "max_results": 3}

    try:
        results = catalog_search_impl(preferences)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.make.title()} {result.model.title()} {result.year}")
            print(f"      Price: ${result.price:,.2f} | Mileage: {result.km:,} km")
            print(f"      Score: {result.similarity_score:.3f}")
            print()
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Search with typos (fuzzy matching)
    print("\n2. Searching with typos (fuzzy matching):")
    preferences = {
        "make": "hond",  # Typo for "honda"
        "model": "civic",
        "max_results": 2,
    }

    try:
        results = catalog_search_impl(preferences)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.make.title()} {result.model.title()} {result.year}")
            print(
                f"      Price: ${result.price:,.2f} | Score: {result.similarity_score:.3f}"
            )
            print()
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Search by features
    print("\n3. Searching for vehicles with specific features:")
    preferences = {"features": ["bluetooth", "air_conditioning"], "max_results": 2}

    try:
        results = catalog_search_impl(preferences)
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.make.title()} {result.model.title()} {result.year}")
            print(
                f"      Price: ${result.price:,.2f} | Features: {list(result.features.keys())}"
            )
            print()
    except Exception as e:
        print(f"   Error: {e}")


def demo_finance_calculation():
    """Demonstrate finance calculation tool."""
    print("\n💰 Finance Calculation Tool Demo")
    print("=" * 50)

    # Test 1: Standard loan calculation
    print("\n1. Standard 5-year loan calculation:")
    inputs = {
        "price": 25000,
        "down_payment": 5000,
        "term_years": 5,
        "interest_rate": 5.5,
    }

    try:
        result = finance_calculation_impl(inputs)
        breakdown = result.payment_breakdown

        print(f"   Vehicle Price: ${inputs['price']:,.2f}")
        print(f"   Down Payment: ${inputs['down_payment']:,.2f}")
        print(f"   Principal: ${breakdown.principal_amount:,.2f}")
        print(f"   Monthly Payment: ${breakdown.monthly_payment:,.2f}")
        print(f"   Total Interest: ${breakdown.total_interest:,.2f}")
        print(f"   Total Payments: ${breakdown.total_payments:,.2f}")
        print("\n   Recommendations:")
        for rec in result.recommendations:
            print(f"   - {rec}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: High down payment scenario
    print("\n2. High down payment scenario:")
    inputs = {
        "price": 30000,
        "down_payment": 15000,
        "term_years": 3,
        "interest_rate": 4.0,
    }

    try:
        result = finance_calculation_impl(inputs)
        breakdown = result.payment_breakdown

        print(f"   Vehicle Price: ${inputs['price']:,.2f}")
        print(f"   Down Payment: ${inputs['down_payment']:,.2f}")
        print(f"   Monthly Payment: ${breakdown.monthly_payment:,.2f}")
        print(f"   Total Interest: ${breakdown.total_interest:,.2f}")
        print("\n   Recommendations:")
        for rec in result.recommendations:
            print(f"   - {rec}")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Full down payment (no financing)
    print("\n3. Full down payment (no financing needed):")
    inputs = {"price": 20000, "down_payment": 20000, "term_years": 5}

    try:
        result = finance_calculation_impl(inputs)
        breakdown = result.payment_breakdown

        print(f"   Vehicle Price: ${inputs['price']:,.2f}")
        print(f"   Down Payment: ${inputs['down_payment']:,.2f}")
        print(f"   Monthly Payment: ${breakdown.monthly_payment:,.2f}")
        print("\n   Recommendations:")
        for rec in result.recommendations:
            print(f"   - {rec}")
    except Exception as e:
        print(f"   Error: {e}")


def demo_tool_registry():
    """Demonstrate tool registry functionality."""
    print("\n🔧 Tool Registry Demo")
    print("=" * 50)

    from tools.registry import get_all_tools, get_tool_names, get_tool

    print("\n1. Available tools:")
    tool_names = get_tool_names()
    for name in tool_names:
        print(f"   - {name}")

    print(f"\n2. Total tools: {len(get_all_tools())}")

    print("\n3. Tool details:")
    for name in tool_names:
        tool = get_tool(name)
        print(f"   {name}:")
        print(f"     Description: {tool.description[:100]}...")
        print(f"     Has function: {tool.func is not None}")
        print(f"     Has schema: {tool.args_schema is not None}")


def main():
    """Run all demos."""
    print("🚗 LangChain Tools Demo")
    print("=" * 60)

    try:
        demo_catalog_search()
        demo_finance_calculation()
        demo_tool_registry()

        print("\n✅ All demos completed successfully!")
        print("\nThese tools are now ready to be used with LangChain agents.")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
