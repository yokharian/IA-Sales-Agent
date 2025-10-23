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

from tools.catalog_search import catalog_search_impl


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


def main():
    """Run all demos."""
    print("🚗 LangChain Tools Demo")
    print("=" * 60)

    try:
        demo_catalog_search()

        print("\n✅ All demos completed successfully!")
        print("\nThese tools are now ready to be used with LangChain agents.")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
