from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Text, Time
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.database.base import Base
import uuid

class DoorModel(Base):
    """Database model for doors/access points"""
    
    __tablename__ = "doors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    door_type = Column(String, nullable=False)  # entrance, exit, bidirectional, emergency
    security_level = Column(String, nullable=False)  # low, medium, high, critical
    status = Column(String, nullable=False, default="active")  # active, inactive, maintenance, emergency_open, emergency_locked
    requires_pin = Column(Boolean, default=False)
    max_attempts = Column(Integer, default=3)
    lockout_duration = Column(Integer, default=300)  # seconds
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_access = Column(DateTime, nullable=True)
    
    # Default access schedule (JSON format)
    default_schedule = Column(Text, nullable=True)  # JSON string with schedule data
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    permissions = relationship("PermissionModel", back_populates="door")
    
    def __repr__(self) -> str:
        return f"<Door(id={self.id}, name='{self.name}', location='{self.location}', security_level='{self.security_level}')>"