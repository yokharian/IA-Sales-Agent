import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import Engine
from typing import Generator

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
