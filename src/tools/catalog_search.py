"""
LangChain tools for vehicle search and recommendations.

This module provides LangChain-compatible tools for searching the vehicle catalog
with advanced filtering, fuzzy matching, and structured results.
"""

from typing import List, Optional, Dict, Any

import rapidfuzz
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db.database import get_session_sync, Vehicle
from db.vehicle_dao import get_makes, get_models, get_models_by_make, search_vehicles


def fuzzy_search_make(make_input: str, threshold: int = 80) -> Optional[str]:
    """
    Find the best matching make using fuzzy search.

    Args:
        make_input: User input for make
        threshold: Minimum similarity score (0-100)

    Returns:
        Best matching make or None if no good match found
    """
    # Get all distinct makes from database using DAO
    all_makes = get_makes(limit=1000)  # Get all makes, not just limited set

    if not all_makes:
        return None

    # Find best match using rapidfuzz
    best_match = rapidfuzz.process.extractOne(
        make_input.lower().strip(),
        [make.lower() for make in all_makes],
        score_cutoff=threshold,
    )

    if best_match:
        # Return the original case make from database
        for make in all_makes:
            if make.lower() == best_match[0]:
                return make

    return None


def fuzzy_search_model(
    model_input: str, make: Optional[str] = None, threshold: int = 80
) -> Optional[str]:
    """
    Find the best matching model using fuzzy search.

    Args:
        model_input: User input for model
        make: Optional make to filter models by
        threshold: Minimum similarity score (0-100)

    Returns:
        Best matching model or None if no good match found
    """
    # Get all distinct models from database using DAO
    if make:
        all_models = get_models_by_make(make, limit=1000)  # Get all models for the make
    else:
        all_models = get_models(limit=1000)  # Get all models

    if not all_models:
        return None

    # Find best match using rapidfuzz
    best_match = rapidfuzz.process.extractOne(
        model_input.lower().strip(),
        [model.lower() for model in all_models],
        score_cutoff=threshold,
    )

    if best_match:
        # Return the original case model from database
        for model in all_models:
            if model.lower() == best_match[0]:
                return model

    return None


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
        description="Required features (e.g., ['bluetooth', 'air_play'])",
    )
    sort_by: Optional[str] = Field(
        default="relevance",
        description="Sort results by: 'price_low', 'price_high', 'year_new', 'km_low'",
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


def catalog_search_impl(preferences: Optional[Dict[str, Any]] = None, **kwargs: Any) -> List[VehicleResult]:
    """
    Search vehicle catalog with filters and fuzzy matching.

    Args:
        preferences: Dictionary of search preferences (can be provided as a single dict positional argument)
        **kwargs: Alternative way to pass individual preference keys

    Returns:
        List of matching vehicles with scores
    """
    # Support both a single dict argument and keyword arguments
    merged_prefs: Dict[str, Any] = {}
    if preferences is not None:
        if not isinstance(preferences, dict):
            raise TypeError("preferences must be a dict if provided")
        merged_prefs.update(preferences)
    if kwargs:
        merged_prefs.update(kwargs)

    # Parse preferences
    prefs = VehiclePreferences(**merged_prefs)

    # Variables to store fuzzy-matched values
    matched_make, matched_model = None, None

    # Fuzzy search for make if provided
    if prefs.make:
        matched_make = fuzzy_search_make(prefs.make)
        if not matched_make:
            # If no good match found, return empty results
            return []

        # If model is also provided, do fuzzy search for model within the matched make
        if prefs.model:
            matched_model = fuzzy_search_model(prefs.model, matched_make)
            if not matched_model:
                # If no good model match found, return empty results
                return []

    elif prefs.model:
        # If only model is provided, do fuzzy search across all models
        matched_model = fuzzy_search_model(prefs.model)
        if not matched_model:
            # If no good match found, return empty results
            return []

    # Use DAO search_vehicles method for database query
    with get_session_sync() as session:
        # Prepare search parameters for DAO
        search_params = {}

        # Use fuzzy-matched make if available
        if matched_make:
            search_params["make"] = matched_make

        # Use fuzzy-matched model if available
        if matched_model:
            search_params["model"] = matched_model

        # Price filters
        if prefs.budget_min is not None:
            search_params["min_price"] = prefs.budget_min
        if prefs.budget_max is not None:
            search_params["max_price"] = prefs.budget_max

        # km filter
        if prefs.km_max is not None:
            search_params["km_max"] = prefs.km_max

        # Note: DAO doesn't have features filter, so we'll filter after query

        # Execute search using DAO
        candidates: List[Vehicle] = search_vehicles(session, **search_params)

    if not candidates:
        return []

    # Apply additional filters that DAO doesn't support
    filtered_candidates = []
    for vehicle in candidates:
        # Apply features filter
        if prefs.features:
            vehicle_has_all_features = True
            for feature in prefs.features:
                if not vehicle.features or not vehicle.features.get(feature, False):
                    vehicle_has_all_features = False
                    break
            if not vehicle_has_all_features:
                continue

        filtered_candidates.append(vehicle)

    if not filtered_candidates:
        return []

    # Apply sorting
    if prefs.sort_by == "price_low":
        filtered_candidates.sort(key=lambda x: x.price)
    elif prefs.sort_by == "price_high":
        filtered_candidates.sort(key=lambda x: x.price, reverse=True)
    elif prefs.sort_by == "year_new":
        filtered_candidates.sort(key=lambda x: x.year, reverse=True)
    elif prefs.sort_by == "km_low":
        filtered_candidates.sort(key=lambda x: x.km)
    else:  # 'model' by default
        filtered_candidates.sort(key=lambda x: x.model, reverse=True)

    # Format results
    results = []
    for vehicle in filtered_candidates[: prefs.max_results]:
        result = VehicleResult(
            stock_id=vehicle.stock_id,
            make=vehicle.make,
            model=vehicle.model,
            year=vehicle.year,
            version=vehicle.version,
            price=vehicle.price,
            km=vehicle.km,
            features=vehicle.features or {},
        )
        results.append(result)

    return results


# Create the LangChain tool
catalog_search_tool = StructuredTool.from_function(
    func=catalog_search_impl,
    name="catalog_search",
    description="""Search the vehicle catalog with advanced filtering and fuzzy matching.
    
    This tool can find vehicles based on:
    - Budget range (budget_min, budget_max)
    - Make and model with typo tolerance (make, model)
    - Maximum mileage (km_max)
    - Required features (features)
    - Sorting preferences (sort_by)
    
    Returns up to 20 vehicles.""",
    args_schema=VehiclePreferences,
)
