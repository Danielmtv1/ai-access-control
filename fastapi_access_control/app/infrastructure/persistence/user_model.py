from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import ARRAY
from app.shared.database.base import Base
from app.domain.entities.user import UserStatus, Role
from datetime import datetime, timezone

class UserModel(Base):
    """SQLAlchemy model for User entity"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    # Store roles as array of strings
    roles = Column(ARRAY(String), nullable=False, default=[])
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True) 