"""
Data access layer for vehicle operations.
"""

from typing import Optional, List
from sqlmodel import Session, select

from models.vehicle import Vehicle


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
        features: Features filter dictionary

    Returns:
        List of Vehicle objects matching criteria
    """
    statement = select(Vehicle)

    if make:
        statement = statement.where(Vehicle.make == make.lower())

    if model:
        statement = statement.where(Vehicle.model == model.lower())

    if min_year:
        statement = statement.where(Vehicle.year >= min_year)

    if max_year:
        statement = statement.where(Vehicle.year <= max_year)

    if min_price:
        statement = statement.where(Vehicle.price >= min_price)

    if max_price:
        statement = statement.where(Vehicle.price <= max_price)

    # Note: Feature filtering would require more complex JSON queries
    # This is a simplified version

    return list(db.exec(statement))
