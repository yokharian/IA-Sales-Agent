import os
from typing import Generator
from typing import Optional, Dict, Any

from sqlalchemy import Column, JSON
from sqlalchemy import Engine
from sqlmodel import SQLModel, Field
from sqlmodel import create_engine, Session

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/commercial_agent"
)

# Create engine
engine: Engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=300,
)


def create_db_and_tables() -> None:
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session


def get_session_sync() -> Session:
    """Get synchronous database session."""
    return Session(engine)


class Vehicle(SQLModel, table=True, extend_existing=True):
    """Vehicle model for storing car inventory data."""

    stock_id: int = Field(primary_key=True, description="Unique stock identifier")
    km: int = Field(description="Kilometers/mileage")
    price: float = Field(description="Vehicle price")
    make: str = Field(description="Vehicle manufacturer")
    model: str = Field(description="Vehicle model")
    year: int = Field(description="Model year")
    version: Optional[str] = Field(default=None, description="Vehicle version/trim")
    largo: Optional[float] = Field(default=None, description="Vehicle length")
    ancho: Optional[float] = Field(default=None, description="Vehicle width")
    altura: Optional[float] = Field(default=None, description="Vehicle height")
    features: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Vehicle features (bluetooth, car_play, etc.)",
    )
