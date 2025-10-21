#!/usr/bin/env python3
"""
Test runner for the commercial agent project.

This script runs all tests and provides a summary of results.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all tests using pytest."""
    project_root = Path(__file__).parent.parent

    # Change to project root directory
    import os

    os.chdir(project_root)

    # Run pytest with verbose output
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "--color=yes"]

    print("Running tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    print("Test modules:")
    print("- test_normalization.py: Data normalization functions")
    print("- test_vehicle_model.py: Vehicle model and database operations")
    print("- test_csv_ingestion.py: CSV processing functionality")
    print("- test_vehicle_dao.py: Data access layer functions")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def main():
    """Main function."""
    success = run_tests()

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
