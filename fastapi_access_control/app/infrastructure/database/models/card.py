from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.database.base import Base
import uuid

class CardModel(Base):
    """Database model for access cards"""
    
    __tablename__ = "cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    card_id = Column(String, unique=True, index=True, nullable=False)  # Physical card identifier
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    card_type = Column(String, nullable=False)  # employee, visitor, contractor, master, temporary
    status = Column(String, nullable=False, default="active")  # active, inactive, suspended, lost, expired
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="cards")
    permissions = relationship("PermissionModel", back_populates="card")
    
    def __repr__(self) -> str:
        return f"<Card(id={self.id}, card_id='{self.card_id}', user_id={self.user_id}, status='{self.status}')>"