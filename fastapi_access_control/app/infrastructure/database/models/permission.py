from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.shared.database.base import Base

class PermissionModel(Base):
    """Database model for access permissions"""
    
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    door_id = Column(Integer, ForeignKey("doors.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)  # Optional: can be user-based or card-based
    status = Column(String, nullable=False, default="active")  # active, inactive, suspended, expired
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    access_schedule = Column(Text, nullable=True)  # JSON string with schedule data
    pin_required = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id], back_populates="permissions")
    door = relationship("DoorModel", back_populates="permissions")
    card = relationship("CardModel", back_populates="permissions")
    created_by_user = relationship("UserModel", foreign_keys=[created_by])
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, user_id={self.user_id}, door_id={self.door_id}, status='{self.status}')>"