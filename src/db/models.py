from typing import Optional, Dict, Any

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


class Vehicle(SQLModel, table=True):
    """Vehicle model for storing car inventory data."""

    stock_id: int = Field(primary_key=True, description="Unique stock identifier")
    make: str = Field(description="Vehicle manufacturer (normalized)")
    model: str = Field(description="Vehicle model (normalized)")
    year: int = Field(description="Model year")
    version: Optional[str] = Field(default=None, description="Vehicle version/trim")
    km: int = Field(description="Kilometers/mileage")
    price: float = Field(description="Vehicle price")
    features: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Vehicle features (bluetooth, car_play, etc.)",
    )
    dims: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON), description="Vehicle dimensions"
    )
    raw_row: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Original CSV row data for reference",
    )
