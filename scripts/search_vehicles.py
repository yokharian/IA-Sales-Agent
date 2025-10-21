#!/usr/bin/env python3
"""
Vehicle search CLI tool.

This script provides a command-line interface for searching vehicles.
"""

import sys
import argparse
import json
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from search.service import VehicleSearchService


def format_vehicle_result(vehicle: dict) -> str:
    """Format a vehicle result for display."""
    result = f"Stock ID: {vehicle['stock_id']}\n"
    result += f"Vehicle: {vehicle['make'].title()} {vehicle['model'].title()}"
    if vehicle.get("version"):
        result += f" {vehicle['version'].upper()}"
    result += f" {vehicle['year']}\n"
    result += f"Price: ${vehicle['price']:,.2f}\n"
    result += f"Mileage: {vehicle['km']:,} km\n"

    if vehicle.get("features"):
        active_features = [k for k, v in vehicle["features"].items() if v]
        if active_features:
            result += f"Features: {', '.join(active_features)}\n"

    result += f"Relevance Score: {vehicle['relevance_score']:.3f}\n"
    result += (
        f"Search Breakdown: Vector={vehicle['search_breakdown']['vector_score']:.3f}, "
    )
    result += f"BM25={vehicle['search_breakdown']['bm25_score']:.3f}, "
    result += f"Fuzzy={vehicle['search_breakdown']['fuzzy_score']:.3f}\n"

    return result


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Search for vehicles")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--max-results", type=int, default=5, help="Maximum number of results to return"
    )
    parser.add_argument("--min-price", type=float, help="Minimum price filter")
    parser.add_argument("--max-price", type=float, help="Maximum price filter")
    parser.add_argument("--make", help="Vehicle make filter")
    parser.add_argument("--model", help="Vehicle model filter")
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--persist-dir", default="./data/chroma", help="Search index directory"
    )

    args = parser.parse_args()

    # Initialize search service
    print("Initializing search service...")
    service = VehicleSearchService(persist_directory=args.persist_dir)
    service.initialize()

    # Perform search
    print(f"Searching for: '{args.query}'")
    results = service.search_vehicles(
        query=args.query,
        max_results=args.max_results,
        min_price=args.min_price,
        max_price=args.max_price,
        make=args.make,
        model=args.model,
    )

    if not results:
        print("No vehicles found matching your criteria.")
        return

    # Display results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"\nFound {len(results)} vehicles:\n")
        for i, vehicle in enumerate(results, 1):
            print(f"--- Result {i} ---")
            print(format_vehicle_result(vehicle))
            print()


if __name__ == "__main__":
    main()
