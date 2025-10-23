"""
Tests for Vehicle model and database operations.
"""

import sys
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, SQLModel

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from db.models import Vehicle
from db.database import get_session_sync


class TestVehicleModel:
    """Test cases for Vehicle model."""

    def test_vehicle_creation(self):
        """Test creating a Vehicle instance."""
        vehicle = Vehicle(
            stock_id=1001,
            make="toyota",
            model="corolla",
            year=2020,
            version="le",
            km=25000,
            price=18500.00,
            features={"bluetooth": True, "car_play": True},
            largo=4.6,
            ancho=1.8,
            altura=1.5,
        )

        assert vehicle.stock_id == 1001
        assert vehicle.make == "toyota"
        assert vehicle.model == "corolla"
        assert vehicle.year == 2020
        assert vehicle.features["bluetooth"] == True
        assert vehicle.largo == 4.6
        assert vehicle.ancho == 1.8
        assert vehicle.altura == 1.5

    def test_vehicle_with_minimal_data(self):
        """Test creating Vehicle with minimal required data."""
        vehicle = Vehicle(
            stock_id=1002,
            make="honda",
            model="civic",
            year=2019,
            km=32000,
            price=16800.00,
        )

        assert vehicle.stock_id == 1002
        assert vehicle.version is None
        assert vehicle.features == {}
        assert vehicle.largo is None
        assert vehicle.ancho is None
        assert vehicle.altura is None


class TestDatabaseOperations:
    """Test cases for database operations."""

    @pytest.fixture
    def test_engine(self):
        """Create test database engine."""
        engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def test_session(self, test_engine):
        """Create test database session."""
        with Session(test_engine) as session:
            yield session

    def test_vehicle_insert(self, test_session):
        """Test inserting a vehicle into database."""
        vehicle = Vehicle(
            stock_id=1001,
            make="toyota",
            model="corolla",
            year=2020,
            km=25000,
            price=18500.00,
            features={"bluetooth": True},
        )

        test_session.add(vehicle)
        test_session.commit()

        # Verify insertion
        retrieved = test_session.get(Vehicle, 1001)
        assert retrieved is not None
        assert retrieved.make == "toyota"
        assert retrieved.features["bluetooth"] == True

    def test_vehicle_update(self, test_session):
        """Test updating a vehicle in database."""
        # Insert initial vehicle
        vehicle = Vehicle(
            stock_id=1002,
            make="honda",
            model="civic",
            year=2019,
            km=32000,
            price=16800.00,
        )

        test_session.add(vehicle)
        test_session.commit()

        # Update vehicle
        vehicle.price = 17000.00
        vehicle.features = {"bluetooth": True}
        vehicle.largo = 4.5
        test_session.commit()

        # Verify update
        retrieved = test_session.get(Vehicle, 1002)
        assert retrieved.price == 17000.00
        assert retrieved.features["bluetooth"] == True
        assert retrieved.largo == 4.5

    def test_vehicle_query(self, test_session):
        """Test querying vehicles from database."""
        # Insert test vehicles
        vehicles = [
            Vehicle(
                stock_id=1001,
                make="toyota",
                model="corolla",
                year=2020,
                km=25000,
                price=18500.00,
            ),
            Vehicle(
                stock_id=1002,
                make="honda",
                model="civic",
                year=2019,
                km=32000,
                price=16800.00,
            ),
            Vehicle(
                stock_id=1003,
                make="toyota",
                model="camry",
                year=2021,
                km=18000,
                price=22000.00,
            ),
        ]

        for vehicle in vehicles:
            test_session.add(vehicle)
        test_session.commit()

        # Query by make
        from sqlmodel import select

        statement = select(Vehicle).where(Vehicle.make == "toyota")
        toyota_vehicles = list(test_session.exec(statement))
        assert len(toyota_vehicles) == 2

        # Query by price range
        statement = select(Vehicle).where(Vehicle.price >= 18000)
        expensive_vehicles = list(test_session.exec(statement))
        assert len(expensive_vehicles) == 2

    def test_get_vehicle_by_id(self, test_session):
        """Test getting vehicle by ID."""
        # Insert test vehicle
        vehicle = Vehicle(
            stock_id=1001,
            make="toyota",
            model="corolla",
            year=2020,
            km=25000,
            price=18500.00,
        )

        test_session.add(vehicle)
        test_session.commit()

        # Test successful retrieval
        from sqlmodel import select

        statement = select(Vehicle).where(Vehicle.stock_id == 1001)
        retrieved = test_session.exec(statement).first()

        assert retrieved is not None
        assert retrieved.stock_id == 1001
        assert retrieved.make == "toyota"
        assert retrieved.model == "corolla"

        # Test non-existent ID
        statement = select(Vehicle).where(Vehicle.stock_id == 9999)
        not_found = test_session.exec(statement).first()
        assert not_found is None
