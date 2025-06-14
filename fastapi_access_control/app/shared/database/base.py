from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
from datetime import datetime, timezone
from typing import Dict, Any

class Base(DeclarativeBase):
    """
    Base class for all database models.
    Provides common functionality and audit fields.
    """
    
    # Campos de auditoría comunes (opcional)
    # created_at = Column(DateTime, default=timezone.utcnow, server_default=func.now())
    # updated_at = Column(DateTime, default=timezone.utcnow, onupdate=timezone.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the model instance into a dictionary mapping column names to their values.
        
        Returns:
            A dictionary where each key is a column name and each value is the corresponding attribute value from the instance.
        """
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
        """String representation of the model"""
        attrs = ', '.join([f"{k}={v!r}" for k, v in self.to_dict().items()])
        return f"{self.__class__.__name__}({attrs})" 