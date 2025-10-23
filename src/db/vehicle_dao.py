"""
Data access layer for vehicle operations.
"""

from typing import List, Optional

from sqlalchemy import distinct
from sqlmodel import Session
from sqlmodel import select

from .database import Vehicle, get_session_sync


def get_makes(limit: int = 5) -> List[str]:
    """
    Get distinct vehicle makes from the database.

    Args:
        limit: Maximum number of makes to return

    Returns:
        List of unique vehicle makes
    """
    with get_session_sync() as session:
        stmt = select(distinct(Vehicle.make)).limit(limit)
        results = session.exec(stmt).all()
        return list(results)


def get_models(limit: int = 5) -> List[str]:
    """
    Get distinct vehicle models from the database.

    Args:
        limit: Maximum number of models to return

    Returns:
        List of unique vehicle models
    """
    with get_session_sync() as session:
        stmt = select(distinct(Vehicle.model)).limit(limit)
        results = session.exec(stmt).all()
        return list(results)


def get_models_by_make(make: str, limit: int = 5) -> List[str]:
    """
    Get distinct vehicle models for a specific make.

    Args:
        make: Vehicle make to filter by
        limit: Maximum number of models to return

    Returns:
        List of unique vehicle models for the specified make
    """
    with get_session_sync() as session:
        stmt = select(distinct(Vehicle.model)).where(Vehicle.make == make).limit(limit)
        results = session.exec(stmt).all()
        return list(results)


def get_vehicle_by_id(db: Session, stock_id: int) -> Optional[Vehicle]:
    """
    Get vehicle by stock_id.

    Args:
        db: Database session
        stock_id: Vehicle stock ID

    Returns:
        Vehicle object or None if not found
    """
    statement = select(Vehicle).where(Vehicle.stock_id == stock_id)
    vehicle = db.exec(statement).first()
    return vehicle


def get_vehicles_by_make_model(db: Session, make: str, model: str) -> List[Vehicle]:
    """
    Get vehicles by make and model.

    Args:
        db: Database session
        make: Vehicle make
        model: Vehicle model

    Returns:
        List of Vehicle objects
    """
    statement = select(Vehicle).where(
        Vehicle.make == make.lower(), Vehicle.model == model.lower()
    )
    return list(db.exec(statement))


def get_vehicles_by_price_range(
    db: Session, min_price: float, max_price: float
) -> List[Vehicle]:
    """
    Get vehicles within a price range.

    Args:
        db: Database session
        min_price: Minimum price
        max_price: Maximum price

    Returns:
        List of Vehicle objects
    """
    statement = select(Vehicle).where(
        Vehicle.price >= min_price, Vehicle.price <= max_price
    )
    return list(db.exec(statement))


def get_vehicles_by_year_range(
    db: Session, min_year: int, max_year: int
) -> List[Vehicle]:
    """
    Get vehicles within a year range.

    Args:
        db: Database session
        min_year: Minimum year
        max_year: Maximum year

    Returns:
        List of Vehicle objects
    """
    statement = select(Vehicle).where(
        Vehicle.year >= min_year, Vehicle.year <= max_year
    )
    return list(db.exec(statement))


def search_vehicles(
    db: Session,
    make: Optional[str] = None,
    model: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    km_max: Optional[int] = None,
    features: Optional[dict] = None,
) -> List[Vehicle]:
    """
    Search vehicles with multiple criteria.

    Args:
        db: Database session
        make: Vehicle make filter
        model: Vehicle model filter
        min_year: Minimum year filter
        max_year: Maximum year filter
        min_price: Minimum price filter
        max_price: Maximum price filter
        km_max: Maximum km filter
        features: Features filter dictionary

    Returns:
        List of Vehicle objects matching criteria
    """
    statement = select(Vehicle)

    if make:
        statement = statement.where(Vehicle.make == make)

    if model:
        statement = statement.where(Vehicle.model == model)

    if min_year:
        statement = statement.where(Vehicle.year >= min_year)

    if max_year:
        statement = statement.where(Vehicle.year <= max_year)

    if min_price:
        statement = statement.where(Vehicle.price >= min_price)

    if max_price:
        statement = statement.where(Vehicle.price <= max_price)

    if km_max:
        statement = statement.where(Vehicle.km <= km_max)

    # Note: Feature filtering would require more complex JSON queries
    # This is a simplified version

    return list(db.exec(statement))
