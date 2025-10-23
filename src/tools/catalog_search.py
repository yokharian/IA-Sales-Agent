"""
LangChain tools for vehicle search and recommendations.

This module provides LangChain-compatible tools for searching the vehicle catalog
with advanced filtering, fuzzy matching, and structured results.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from sqlalchemy import and_, or_, text
from sqlmodel import Session, select

from search.service import VehicleSearchService
from db.models import Vehicle
from db.database import get_session_sync


class VehiclePreferences(BaseModel):
    """Input schema for vehicle search preferences."""

    budget_min: Optional[float] = Field(
        default=None, description="Minimum budget in USD", ge=0
    )
    budget_max: Optional[float] = Field(
        default=None, description="Maximum budget in USD", ge=0
    )
    make: Optional[str] = Field(
        default=None,
        description="Preferred vehicle make (supports typos and fuzzy matching)",
    )
    model: Optional[str] = Field(
        default=None,
        description="Preferred vehicle model (supports typos and fuzzy matching)",
    )
    km_max: Optional[int] = Field(
        default=None, description="Maximum kilometers/mileage", ge=0
    )
    features: Optional[List[str]] = Field(
        default=None,
        description="Required features (e.g., ['bluetooth', 'air_conditioning'])",
    )
    sort_by: Optional[str] = Field(
        default="relevance",
        description="Sort results by: 'relevance', 'price_low', 'price_high', 'year_new', 'km_low'",
    )
    max_results: Optional[int] = Field(
        default=5, description="Maximum number of results to return", ge=1, le=20
    )


class VehicleResult(BaseModel):
    """Output schema for vehicle search results."""

    stock_id: int = Field(description="Unique vehicle stock ID")
    make: str = Field(description="Vehicle make")
    model: str = Field(description="Vehicle model")
    year: int = Field(description="Model year")
    version: Optional[str] = Field(description="Vehicle version/trim")
    price: float = Field(description="Price in USD")
    km: int = Field(description="Mileage in kilometers")
    features: Dict[str, bool] = Field(description="Available features")
    similarity_score: float = Field(
        description="Relevance score (0-1, higher is better)", ge=0, le=1
    )


def catalog_search_impl(preferences: Dict[str, Any]) -> List[VehicleResult]:
    """
    Search vehicle catalog with filters and fuzzy matching.

    Args:
        preferences: Dictionary of search preferences

    Returns:
        List of matching vehicles with scores
    """
    # Parse preferences
    prefs = VehiclePreferences(**preferences)

    # Initialize search service
    search_service = VehicleSearchService()
    search_service.initialize()

    # Build SQL query with hard filters
    with get_session_sync() as session:
        query = select(Vehicle)
        filters = []

        # Price filters
        if prefs.budget_min is not None:
            filters.append(Vehicle.price >= prefs.budget_min)
        if prefs.budget_max is not None:
            filters.append(Vehicle.price <= prefs.budget_max)

        # Mileage filter
        if prefs.km_max is not None:
            filters.append(Vehicle.km <= prefs.km_max)

        # Feature filters using JSONB
        if prefs.features:
            for feature in prefs.features:
                # Use raw SQL for JSONB boolean comparison
                filters.append(text(f"vehicle.features->>'{feature}' = 'true'"))

        # Apply filters
        if filters:
            query = query.where(and_(*filters))

        # Execute query to get candidates
        candidates = list(session.exec(query))

    if not candidates:
        return []

    # Apply hybrid search if make/model specified
    if prefs.make or prefs.model:
        search_query = f"{prefs.make or ''} {prefs.model or ''}".strip()
        search_results = search_service.search_vehicles(
            query=search_query,
            max_results=prefs.max_results * 2,  # Get more for sorting
        )

        # Create a mapping of stock_id to search result
        search_map = {result["stock_id"]: result for result in search_results}

        # Filter candidates to only include those found by search
        ranked_candidates = []
        for candidate in candidates:
            if candidate.stock_id in search_map:
                search_result = search_map[candidate.stock_id]
                ranked_candidates.append((candidate, search_result["relevance_score"]))

        # Sort by search score
        ranked_candidates.sort(key=lambda x: x[1], reverse=True)
    else:
        # No make/model search, just use candidates as-is
        ranked_candidates = [(candidate, 1.0) for candidate in candidates]

    # Apply sorting
    if prefs.sort_by == "price_low":
        ranked_candidates.sort(key=lambda x: x[0].price)
    elif prefs.sort_by == "price_high":
        ranked_candidates.sort(key=lambda x: x[0].price, reverse=True)
    elif prefs.sort_by == "year_new":
        ranked_candidates.sort(key=lambda x: x[0].year, reverse=True)
    elif prefs.sort_by == "km_low":
        ranked_candidates.sort(key=lambda x: x[0].km)
    # 'relevance' is already sorted by search score

    # Format results
    results = []
    for vehicle, score in ranked_candidates[: prefs.max_results]:

        result = VehicleResult(
            stock_id=vehicle.stock_id,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            version=vehicle.version,
            price=vehicle.price,
            km=vehicle.km,
            features=vehicle.features or {},
            similarity_score=score,
        )
        results.append(result)

    return results


# Create the LangChain tool
catalog_search_tool = Tool(
    name="catalog_search",
    func=catalog_search_impl,
    description="""Search the vehicle catalog with advanced filtering and fuzzy matching.
    
    This tool can find vehicles based on:
    - Budget range (budget_min, budget_max)
    - Make and model with typo tolerance (make, model)
    - Maximum mileage (km_max)
    - Required features (features)
    - Sorting preferences (sort_by)
    
    The tool uses hybrid search combining semantic similarity, keyword matching,
    and fuzzy text matching to handle typos and find relevant vehicles even
    with imperfect input.
    
    Returns up to 20 vehicles with relevance scores
    explaining why each vehicle matches the criteria.""",
    args_schema=VehiclePreferences,
)
