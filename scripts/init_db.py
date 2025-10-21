#!/usr/bin/env python3
"""
Database initialization script.

This script creates the database tables and can be used for setup.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from db.database import create_db_and_tables
from models.vehicle import Vehicle


def main():
    """Create database tables."""
    print("Creating database tables...")
    create_db_and_tables()
    print("Database tables created successfully!")


if __name__ == "__main__":
    main()
