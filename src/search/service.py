"""
Search service for vehicle recommendations.

This module provides a high-level interface for vehicle search operations.
"""

from typing import List, Dict, Any, Optional
from search.engine import VehicleSearchEngine


class VehicleSearchService:
    """
    High-level service for vehicle search operations.

    Provides a simplified interface for common search operations
    and handles search engine initialization.
    """

    def __init__(self, persist_directory: str = "./data/chroma"):
        """
        Initialize the search service.

        Args:
            persist_directory: Directory to persist search index
        """
        self.engine = VehicleSearchEngine(persist_directory)
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the search engine with vehicle data."""
        if not self._initialized:
            self.engine.build_index()
            self._initialized = True

    def search_vehicles(
        self,
        query: str,
        max_results: int = 5,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for vehicles with optional filters.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            min_price: Minimum price filter
            max_price: Maximum price filter
            make: Vehicle make filter
            model: Vehicle model filter

        Returns:
            List of vehicle search results
        """
        if not self._initialized:
            self.initialize()

        # Perform search
        results = self.engine.search(query, k=max_results * 2)  # Get more for filtering

        # Apply filters
        filtered_results = []
        for result in results:
            vehicle = result["vehicle"]
            metadata = vehicle.metadata

            # Apply price filters
            if min_price is not None and metadata.get("price", 0) < min_price:
                continue
            if max_price is not None and metadata.get("price", 0) > max_price:
                continue

            # Apply make filter
            if make and metadata.get("make", "").lower() != make.lower():
                continue

            # Apply model filter
            if model and metadata.get("model", "").lower() != model.lower():
                continue

            # Format result
            formatted_result = {
                "stock_id": metadata["stock_id"],
                "make": metadata["make"],
                "model": metadata["model"],
                "year": metadata["year"],
                "version": metadata.get("version"),
                "price": metadata["price"],
                "km": metadata["km"],
                "features": metadata.get("features", {}),
                "search_text": vehicle.page_content,
                "relevance_score": result["combined_score"],
                "search_breakdown": {
                    "vector_score": result["vector_score"],
                    "bm25_score": result["bm25_score"],
                    "fuzzy_score": result["fuzzy_score"],
                },
            }

            filtered_results.append(formatted_result)

            if len(filtered_results) >= max_results:
                break

        return filtered_results

    def get_vehicle_details(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific vehicle.

        Args:
            stock_id: Vehicle stock ID

        Returns:
            Vehicle details if found, None otherwise
        """
        if not self._initialized:
            self.initialize()

        return self.engine.get_vehicle_by_stock_id(stock_id)

    def search_similar_vehicles(
        self, stock_id: int, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find vehicles similar to a specific vehicle.

        Args:
            stock_id: Reference vehicle stock ID
            max_results: Maximum number of similar vehicles to return

        Returns:
            List of similar vehicles
        """
        if not self._initialized:
            self.initialize()

        # Get the reference vehicle
        reference_vehicle = self.engine.get_vehicle_by_stock_id(stock_id)
        if not reference_vehicle:
            return []

        # Use the vehicle's search text as query
        query = reference_vehicle["text"]

        # Search for similar vehicles
        results = self.engine.search(query, k=max_results + 1)  # +1 to exclude self

        # Filter out the reference vehicle and format results
        similar_vehicles = []
        for result in results:
            vehicle = result["vehicle"]
            metadata = vehicle.metadata

            if metadata["stock_id"] != stock_id:
                similar_vehicles.append(
                    {
                        "stock_id": metadata["stock_id"],
                        "make": metadata["make"],
                        "model": metadata["model"],
                        "year": metadata["year"],
                        "version": metadata.get("version"),
                        "price": metadata["price"],
                        "km": metadata["km"],
                        "features": metadata.get("features", {}),
                        "similarity_score": result["combined_score"],
                    }
                )

                if len(similar_vehicles) >= max_results:
                    break

        return similar_vehicles
