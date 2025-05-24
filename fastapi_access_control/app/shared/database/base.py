from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
from datetime import datetime
from typing import Dict, Any

class Base(DeclarativeBase):
    """
    Base class for all database models.
    Provides common functionality and audit fields.
    """
    
    # Campos de auditoría comunes (opcional)
    # created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}
    
    def __repr__(self) -> str:
        """String representation of the model"""
        attrs = ', '.join([f"{k}={v!r}" for k, v in self.to_dict().items()])
        return f"{self.__class__.__name__}({attrs})" 