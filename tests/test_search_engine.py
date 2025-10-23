"""
Tests for vehicle search engine.
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from search.engine import VehicleSearchEngine
from search.service import VehicleSearchService
from db.models import Vehicle


class TestVehicleSearchEngine:
    """Test cases for VehicleSearchEngine."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_vehicles(self):
        """Create mock vehicle data for testing."""
        return [
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
        ]

    def test_engine_initialization(self, temp_dir):
        """Test search engine initialization."""
        engine = VehicleSearchEngine(persist_directory=temp_dir)

        assert engine.persist_directory == temp_dir
        assert engine.embeddings is not None
        # vector_store may be None or loaded from existing index
        assert engine.bm25_retriever is None
        assert engine.vehicles_corpus == []
        assert engine.vehicles_metadata == []

    def test_prepare_documents(self, temp_dir, mock_vehicles):
        """Test document preparation."""
        engine = VehicleSearchEngine(persist_directory=temp_dir)

        # Mock the database session
        with patch("search.engine.get_session_sync") as mock_session:
            mock_session.return_value.__enter__.return_value.exec.return_value = (
                mock_vehicles
            )

            documents = engine._prepare_documents()

        assert len(documents) == 3

        # Check first document
        doc = documents[0]
        assert "toyota corolla le 2020 25000km bluetooth car_play" in doc.page_content
        assert doc.metadata["stock_id"] == 1001
        assert doc.metadata["make"] == "toyota"
        assert doc.metadata["price"] == 18500.00

        # Check corpus and metadata
        assert len(engine.vehicles_corpus) == 3
        assert len(engine.vehicles_metadata) == 3

    def test_normalize_scores(self, temp_dir):
        """Test score normalization."""
        engine = VehicleSearchEngine(persist_directory=temp_dir)

        scores = [0.1, 0.5, 0.9, 0.3]
        normalized = engine._normalize_scores(scores)

        assert len(normalized) == 4
        assert min(normalized) == 0.0
        assert max(normalized) == 1.0
        assert normalized[0] == 0.0  # 0.1 -> 0.0
        assert normalized[2] == 1.0  # 0.9 -> 1.0

    def test_combine_scores(self, temp_dir):
        """Test score combination logic."""
        engine = VehicleSearchEngine(persist_directory=temp_dir)

        # Mock results
        vector_results = [
            (Mock(metadata={"stock_id": 1001}), 0.8),
            (Mock(metadata={"stock_id": 1002}), 0.6),
        ]
        bm25_results = [
            Mock(metadata={"stock_id": 1001, "score": 0.7}),
            Mock(metadata={"stock_id": 1003, "score": 0.9}),
        ]
        fuzzy_results = [
            ("toyota corolla", 0.9, {"stock_id": 1001}),
            ("honda civic", 0.8, {"stock_id": 1002}),
        ]

        combined = engine._combine_scores(vector_results, bm25_results, fuzzy_results)

        assert len(combined) == 3  # Should have 3 unique stock_ids

        # Check that combined scores are calculated
        for result in combined:
            assert "combined_score" in result
            assert 0 <= result["combined_score"] <= 1


class TestVehicleSearchService:
    """Test cases for VehicleSearchService."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_service_initialization(self, temp_dir):
        """Test search service initialization."""
        service = VehicleSearchService(persist_directory=temp_dir)

        assert service.engine is not None
        assert not service._initialized

    def test_search_vehicles_basic(self, temp_dir):
        """Test basic vehicle search."""
        service = VehicleSearchService(persist_directory=temp_dir)

        # Mock the search engine
        mock_results = [
            {
                "vehicle": Mock(
                    metadata={
                        "stock_id": 1001,
                        "make": "toyota",
                        "model": "corolla",
                        "year": 2020,
                        "price": 18500.00,
                        "km": 25000,
                        "version": "le",
                        "features": {"bluetooth": True},
                    }
                ),
                "combined_score": 0.9,
                "vector_score": 0.8,
                "bm25_score": 0.7,
                "fuzzy_score": 0.6,
            }
        ]

        with patch.object(service.engine, "search", return_value=mock_results):
            with patch.object(service, "_initialized", True):
                results = service.search_vehicles("toyota corolla")

        assert len(results) == 1
        result = results[0]
        assert result["stock_id"] == 1001
        assert result["make"] == "toyota"
        assert result["model"] == "corolla"
        assert result["relevance_score"] == 0.9
        assert "search_breakdown" in result

    def test_search_vehicles_with_filters(self, temp_dir):
        """Test vehicle search with filters."""
        service = VehicleSearchService(persist_directory=temp_dir)

        # Mock results with different prices
        mock_results = [
            {
                "vehicle": Mock(
                    metadata={
                        "stock_id": 1001,
                        "make": "toyota",
                        "model": "corolla",
                        "year": 2020,
                        "price": 15000.00,
                        "km": 25000,
                        "version": "le",
                        "features": {},
                    }
                ),
                "combined_score": 0.9,
                "vector_score": 0.8,
                "bm25_score": 0.7,
                "fuzzy_score": 0.6,
            },
            {
                "vehicle": Mock(
                    metadata={
                        "stock_id": 1002,
                        "make": "honda",
                        "model": "civic",
                        "year": 2019,
                        "price": 25000.00,
                        "km": 32000,
                        "version": "lx",
                        "features": {},
                    }
                ),
                "combined_score": 0.8,
                "vector_score": 0.7,
                "bm25_score": 0.6,
                "fuzzy_score": 0.5,
            },
        ]

        with patch.object(service.engine, "search", return_value=mock_results):
            with patch.object(service, "_initialized", True):
                # Test price filter
                results = service.search_vehicles(
                    "car", min_price=20000.00, max_price=30000.00
                )

        assert len(results) == 1
        assert results[0]["stock_id"] == 1002  # Only the expensive one should pass

    def test_get_vehicle_details(self, temp_dir):
        """Test getting vehicle details by stock_id."""
        service = VehicleSearchService(persist_directory=temp_dir)

        mock_vehicle = {
            "stock_id": 1001,
            "text": "toyota corolla le 2020 25000km",
            "make": "toyota",
            "model": "corolla",
        }

        with patch.object(
            service.engine, "get_vehicle_by_stock_id", return_value=mock_vehicle
        ):
            with patch.object(service, "_initialized", True):
                result = service.get_vehicle_details(1001)

        assert result == mock_vehicle

    def test_search_similar_vehicles(self, temp_dir):
        """Test finding similar vehicles."""
        service = VehicleSearchService(persist_directory=temp_dir)

        # Mock reference vehicle
        mock_reference = {
            "stock_id": 1001,
            "text": "toyota corolla le 2020 25000km",
            "make": "toyota",
            "model": "corolla",
        }

        # Mock search results
        mock_results = [
            {
                "vehicle": Mock(
                    metadata={
                        "stock_id": 1002,
                        "make": "honda",
                        "model": "civic",
                        "year": 2019,
                        "price": 16800.00,
                        "km": 32000,
                        "version": "lx",
                        "features": {},
                    }
                ),
                "combined_score": 0.8,
                "vector_score": 0.7,
                "bm25_score": 0.6,
                "fuzzy_score": 0.5,
            }
        ]

        with patch.object(
            service.engine, "get_vehicle_by_stock_id", return_value=mock_reference
        ):
            with patch.object(service.engine, "search", return_value=mock_results):
                with patch.object(service, "_initialized", True):
                    results = service.search_similar_vehicles(1001)

        assert len(results) == 1
        assert results[0]["stock_id"] == 1002
        assert results[0]["similarity_score"] == 0.8
