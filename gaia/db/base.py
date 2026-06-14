"""Declarative base for all GAIA SQLAlchemy ORM models.

Every model module must import Base from here so that
alembic/env.py can discover all tables via Base.metadata.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base.  All GAIA ORM models inherit from this."""
    pass
