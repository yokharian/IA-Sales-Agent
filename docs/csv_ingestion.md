# CSV Ingestion and Database Setup

This module provides a complete CSV ingestion pipeline for vehicle data with PostgreSQL storage and Redis caching.

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
cp .env.example .env

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

### Programmatic Usage

```python
from src.db.database import get_session_sync, create_db_and_tables
from src.db.vehicle_dao import get_vehicle_by_id, search_vehicles
from src.db.models import Vehicle

# Create tables
create_db_and_tables()

# Get a vehicle by ID
with get_session_sync() as session:
	vehicle = get_vehicle_by_id(session, 1001)
	print(f"Found: {vehicle.make} {vehicle.model}")

# Search vehicles
with get_session_sync() as session:
	results = search_vehicles(
		session,
		make="toyota",
		min_year=2020,
		max_price=20000
	)
	for vehicle in results:
		print(f"{vehicle.make} {vehicle.model} - ${vehicle.price}")
```

## CSV Format

The CSV file should contain the following columns:

| Column    | Type   | Required | Description               |
| --------- | ------ | -------- | ------------------------- |
| stock_id  | int    | Yes      | Unique vehicle identifier |
| make      | string | Yes      | Vehicle manufacturer      |
| model     | string | Yes      | Vehicle model             |
| year      | int    | Yes      | Model year                |
| version   | string | No       | Vehicle version/trim      |
| km        | int    | Yes      | Mileage in kilometers     |
| price     | float  | Yes      | Vehicle price             |
| bluetooth | string | No       | Bluetooth feature (Sí/No) |
| car_play  | string | No       | CarPlay feature (Sí/No)   |
| largo     | float  | No       | Vehicle length in meters  |
| ancho     | float  | No       | Vehicle width in meters   |
| altura    | float  | No       | Vehicle height in meters  |

### Example CSV

```csv
stock_id,km,price,make,model,year,version,bluetooth,largo,ancho,altura,car_play
243587,77400,461999.0,Volkswagen,Touareg,2018,3.0 V6 TDI WOLFSBURG EDITION AUTO 4WD,Sí,4801.0,1940.0,1709.0,
229702,102184,660999.0,Land Rover,Discovery Sport,2018,2.0 HSE LUXURY AUTO 4WD,Sí,4599.0,2069.0,1724.0,
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
pytest tests/test_normalization.py -v
pytest tests/test_vehicle_model.py -v
pytest tests/test_csv_ingestion.py -v
```

## Architecture

```
src/
├── db/
│   ├── models.py             # SQLModel Vehicle definition
│   ├── database.py          # Database connection and session management
│   └── vehicle_dao.py       # Data access layer
└── utils/
    └── normalization.py     # Data normalization functions

scripts/
├── ingest_csv.py           # Main CSV ingestion script
├── init_db.py             # Database initialization
└── run_tests.py           # Test runner

tests/
├── test_normalization.py  # Normalization function tests
├── test_vehicle_model.py  # Model and database tests
├── test_csv_ingestion.py  # CSV processing tests
└── test_vehicle_dao.py    # Data access layer tests
```

## Performance Considerations

- **Batch Processing**: Default batch size of 500 rows for optimal performance
- **Connection Pooling**: SQLAlchemy connection pooling for database efficiency
- **Memory Management**: Streaming CSV processing for large files
- **Pydantic Validation**: Efficient validation using TypeAdapter.validate_python

## Next Steps

This module provides the foundation for the vehicle search system. The next task will implement vector embeddings and semantic search capabilities on top of this data structure.
