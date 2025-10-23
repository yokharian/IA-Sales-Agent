# CSV Ingestion and Database Setup

This module provides a complete CSV ingestion pipeline for vehicle data with PostgreSQL storage.

## Features

- **Robust CSV Parsing**: Handles various CSV formats with error recovery
- **Data Normalization**: Automatic text normalization (lowercase, accent removal)
- **PostgreSQL Integration**: Uses SQLModel for type-safe database operations
- **Batch Processing**: Efficient batch inserts with configurable batch sizes
- **Error Handling**: Comprehensive error logging without halting processing
- **Comprehensive Testing**: Full test suite with pytest

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
# Copy the example environment file
cp env.example .env

# Edit .env with your database settings
DATABASE_URL=postgresql://postgres:password@localhost:5432/commercial_agent
```

3. Set up PostgreSQL database:

```bash
# Create database
createdb commercial_agent

# Initialize tables
python scripts/init_db.py
```

## Usage

### Basic CSV Ingestion

```bash
# Ingest a CSV file
python scripts/ingest_csv.py data/sample_vehicles.csv

# With custom batch size
python scripts/ingest_csv.py data/sample_vehicles.csv --batch-size 1000

# Create tables and ingest
python scripts/ingest_csv.py data/sample_vehicles.csv --create-tables
```

## Data Normalization

The system automatically normalizes data:

- **Text Fields**: Converted to lowercase, accents removed using unidecode
- **Boolean Fields**: "Sí", "si", "yes", "true", "1" → True; others → False
- **Numeric Fields**: Safe conversion with fallback to None for invalid data
- **Missing Data**: Optional fields default to None or empty values

## Error Handling

- **Invalid Data**: Logged to `ingestion_errors.log` without halting processing
- **Missing Columns**: Gracefully handled with default values
- **Type Mismatches**: Safe conversion with fallback to None
- **Database Errors**: Transaction rollback with detailed error logging
- **Pydantic Validation**: TypeAdapter.validate_python ensures data integrity

## Testing

Run the complete test suite:

```bash
# Run all tests
python scripts/run_tests.py

# Run specific test modules
pytest tests/test_csv_ingestion.py -v
pytest tests/test_vehicle_dao.py -v
```

## Architecture

```
src/
├── db/
│   ├── database.py          # Database connection and session management
│   └── vehicle_dao.py       # Data access layer

scripts/
├── ingest_csv.py           # Main CSV ingestion script
├── init_db.py             # Database initialization
└── run_tests.py           # Test runner

tests/
├── test_csv_ingestion.py  # CSV processing tests
└── test_vehicle_dao.py    # Data access layer tests
```

---

**Script:** `scripts/ingest_csv.py`  
**Database:** PostgreSQL with SQLModel  
**Testing:** `tests/test_csv_ingestion.py`
