"""
SQLAlchemy declarative base for all ORM models.

Import Base from here when defining new models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
