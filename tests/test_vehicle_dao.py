"""
Tests for vehicle data access layer.
"""

import pytest
import sys
from pathlib import Path
from sqlmodel import Session, create_engine, SQLModel

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from db.database import Vehicle
from db.vehicle_dao import (
    get_vehicle_by_id,
    get_vehicles_by_make_model,
    get_vehicles_by_price_range,
    get_vehicles_by_year_range,
    search_vehicles,
)


class TestVehicleDAO:
    """Test cases for vehicle data access layer."""

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

    @pytest.fixture
    def sample_vehicles(self, test_session):
        """Create sample vehicles for testing."""
        vehicles = [
            Vehicle(
                stock_id=1001,
                make="toyota",
                model="corolla",
                year=2020,
                version="le",
                km=25000,
                price=18500.00,
                features={"bluetooth": True, "car_play": True},
            ),
            Vehicle(
                stock_id=1002,
                make="honda",
                model="civic",
                year=2019,
                version="lx",
                km=32000,
                price=16800.00,
                features={"bluetooth": True, "car_play": False},
            ),
            Vehicle(
                stock_id=1003,
                make="toyota",
                model="camry",
                year=2021,
                version="se",
                km=18000,
                price=22000.00,
                features={"bluetooth": True, "car_play": True},
            ),
            Vehicle(
                stock_id=1004,
                make="ford",
                model="focus",
                year=2018,
                version="base",
                km=45000,
                price=14200.00,
                features={"bluetooth": False, "car_play": False},
            ),
        ]

        for vehicle in vehicles:
            test_session.add(vehicle)
        test_session.commit()
        return vehicles

    def test_get_vehicle_by_id_success(self, test_session, sample_vehicles):
        """Test successful vehicle retrieval by ID."""
        vehicle = get_vehicle_by_id(test_session, 1001)

        assert vehicle is not None
        assert vehicle.stock_id == 1001
        assert vehicle.make == "toyota"
        assert vehicle.model == "corolla"
        assert vehicle.year == 2020
        assert vehicle.price == 18500.00

    def test_get_vehicle_by_id_not_found(self, test_session, sample_vehicles):
        """Test vehicle retrieval with non-existent ID."""
        vehicle = get_vehicle_by_id(test_session, 9999)
        assert vehicle is None

    def test_get_vehicles_by_make_model(self, test_session, sample_vehicles):
        """Test getting vehicles by make and model."""
        toyota_corollas = get_vehicles_by_make_model(test_session, "toyota", "corolla")

        assert len(toyota_corollas) == 1
        assert toyota_corollas[0].stock_id == 1001
        assert toyota_corollas[0].make == "toyota"
        assert toyota_corollas[0].model == "corolla"

    def test_get_vehicles_by_price_range(self, test_session, sample_vehicles):
        """Test getting vehicles within price range."""
        expensive_vehicles = get_vehicles_by_price_range(test_session, 18000, 25000)

        assert len(expensive_vehicles) == 2
        stock_ids = [v.stock_id for v in expensive_vehicles]
        assert 1001 in stock_ids  # Toyota Corolla - $18,500
        assert 1003 in stock_ids  # Toyota Camry - $22,000

    def test_get_vehicles_by_year_range(self, test_session, sample_vehicles):
        """Test getting vehicles within year range."""
        recent_vehicles = get_vehicles_by_year_range(test_session, 2020, 2021)

        assert len(recent_vehicles) == 2
        stock_ids = [v.stock_id for v in recent_vehicles]
        assert 1001 in stock_ids  # 2020 Toyota Corolla
        assert 1003 in stock_ids  # 2021 Toyota Camry

    def test_search_vehicles_by_make(self, test_session, sample_vehicles):
        """Test searching vehicles by make."""
        toyota_vehicles = search_vehicles(test_session, make="toyota")

        assert len(toyota_vehicles) == 2
        stock_ids = [v.stock_id for v in toyota_vehicles]
        assert 1001 in stock_ids  # Toyota Corolla
        assert 1003 in stock_ids  # Toyota Camry

    def test_search_vehicles_by_price_and_year(self, test_session, sample_vehicles):
        """Test searching vehicles with multiple criteria."""
        results = search_vehicles(
            test_session, min_price=15000, max_price=20000, min_year=2019, max_year=2020
        )

        assert len(results) == 2
        stock_ids = [v.stock_id for v in results]
        assert 1001 in stock_ids  # 2020 Toyota Corolla - $18,500
        assert 1002 in stock_ids  # 2019 Honda Civic - $16,800

    def test_search_vehicles_no_results(self, test_session, sample_vehicles):
        """Test searching vehicles with no matching criteria."""
        results = search_vehicles(test_session, make="bmw", min_price=50000)

        assert len(results) == 0
