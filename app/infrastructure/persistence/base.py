from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
from datetime import datetime
from typing import Dict, Any

class SqlAlchemyBase(DeclarativeBase):
    """Base class for SQLAlchemy models in infrastructure."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
        """String representation of the model."""
        attrs = ', '.join([f"{k}={v!r}" for k, v in self.to_dict().items()])
        return f"{self.__class__.__name__}({attrs})" 