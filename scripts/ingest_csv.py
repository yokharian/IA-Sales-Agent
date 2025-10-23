#!/usr/bin/env python3
"""
CSV Ingestion Script for Vehicle Data

This script processes CSV files containing vehicle data and ingests them
into the PostgreSQL database with proper normalization and error handling.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from sqlmodel import Session

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from db.models import Vehicle
from db.database import engine, create_db_and_tables
from utils.normalization import normalize_text, parse_boolean, safe_int, safe_float


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ingestion_errors.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def process_vehicle_row(row: pd.Series) -> Dict[str, Any]:
    """
    Process a single CSV row and return normalized vehicle data.

    Args:
        row: Pandas Series representing a CSV row

    Returns:
        Dictionary with normalized vehicle data
    """
    try:
        # Extract and normalize basic fields
        stock_id = safe_int(row.get("stock_id"))
        make = normalize_text(row.get("make"))
        model = normalize_text(row.get("model"))
        year = safe_int(row.get("year"))
        version = (
            normalize_text(row.get("version")) if pd.notna(row.get("version")) else None
        )
        km = safe_int(row.get("km"))
        price = safe_float(row.get("price"))

        # Process features
        features = {}
        feature_columns = [
            "bluetooth",
            "car_play",
            "air_conditioning",
            "power_steering",
            "power_windows",
            "central_locking",
            "alarm",
            "radio",
        ]

        for feature in feature_columns:
            if feature in row:
                features[feature] = parse_boolean(row[feature])

        # Process dimensions if available
        dims = None
        if "dims" in row and pd.notna(row["dims"]):
            try:
                dims = (
                    eval(row["dims"]) if isinstance(row["dims"], str) else row["dims"]
                )
            except:
                dims = None

        # Store raw row data
        raw_row = row.to_dict()

        return {
            "stock_id": stock_id,
            "make": make,
            "model": model,
            "year": year,
            "version": version,
            "km": km,
            "price": price,
            "features": features,
            "dims": dims,
            "raw_row": raw_row,
        }

    except Exception as e:
        logger.error(
            f"Error processing row with stock_id {row.get('stock_id', 'unknown')}: {e}"
        )
        raise


def ingest_csv(filepath: str, batch_size: int = 500) -> None:
    """
    Ingest CSV file into the database.

    Args:
        filepath: Path to CSV file
        batch_size: Number of rows to process in each batch
    """
    filepath = Path(filepath)

    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return

    logger.info(f"Starting ingestion of {filepath}")

    try:
        # Read CSV file
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} rows from CSV")

        # Create database tables if they don't exist
        create_db_and_tables()

        processed_count = 0
        error_count = 0

        with Session(engine) as session:
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i : i + batch_size]
                batch_vehicles = []

                for _, row in batch_df.iterrows():
                    try:
                        vehicle_data = process_vehicle_row(row)

                        # Create Vehicle instance
                        vehicle = Vehicle(**vehicle_data)
                        batch_vehicles.append(vehicle)

                    except Exception as e:
                        error_count += 1
                        logger.error(
                            f"Failed to process row {i + len(batch_vehicles)}: {e}"
                        )
                        continue

                # Batch insert/update using merge
                for vehicle in batch_vehicles:
                    session.merge(vehicle)

                session.commit()
                processed_count += len(batch_vehicles)

                logger.info(
                    f"Processed batch {i//batch_size + 1}: {len(batch_vehicles)} vehicles"
                )

        logger.info(
            f"Ingestion completed. Processed: {processed_count}, Errors: {error_count}"
        )

    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        raise


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Ingest vehicle CSV data into database"
    )
    parser.add_argument("filepath", help="Path to CSV file")
    parser.add_argument(
        "--batch-size", type=int, default=500, help="Batch size for processing"
    )
    parser.add_argument(
        "--create-tables", action="store_true", help="Create database tables"
    )

    args = parser.parse_args()

    if args.create_tables:
        create_db_and_tables()
        logger.info("Database tables created")

    ingest_csv(args.filepath, args.batch_size)


if __name__ == "__main__":
    main()
