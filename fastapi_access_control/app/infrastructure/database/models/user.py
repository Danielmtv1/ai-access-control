from sqlalchemy import Column, String, Boolean, DateTime, func, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.database.base import Base
import uuid

class UserModel(Base):
    """Database model for users"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    roles = Column(ARRAY(String), nullable=False, default=[])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    cards = relationship("CardModel", back_populates="user")
    permissions = relationship("PermissionModel", foreign_keys="PermissionModel.user_id", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', roles={self.roles})>" 