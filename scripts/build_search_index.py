#!/usr/bin/env python3
"""
Build search index script.

This script builds the search index from vehicle data in the database.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from search.service import VehicleSearchService


def main():
    """Build the search index."""
    parser = argparse.ArgumentParser(description="Build vehicle search index")
    parser.add_argument(
        "--persist-dir",
        default="./data/chroma",
        help="Directory to persist the search index",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force rebuild even if index exists"
    )

    args = parser.parse_args()

    print("Initializing vehicle search service...")
    service = VehicleSearchService(persist_directory=args.persist_dir)

    if args.force:
        print("Force rebuild requested - removing existing index...")
        import shutil

        if Path(args.persist_dir).exists():
            shutil.rmtree(args.persist_dir)

    print("Building search index...")
    service.initialize()

    print("Search index built successfully!")
    print(f"Index location: {args.persist_dir}")


if __name__ == "__main__":
    main()
