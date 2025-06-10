from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List
from uuid import UUID
import re

class Email(BaseModel):
    """Value object for email validation"""
    value: EmailStr

    def __str__(self) -> str:
        return self.value

    @classmethod
    def create(cls, email: str) -> 'Email':
        """Factory method to create an Email value object"""
        return cls(value=email)

class Password(BaseModel):
    """Value object for password validation"""
    value: str

    @field_validator('value')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        return v

    def __str__(self) -> str:
        return self.value

    @classmethod
    def create(cls, password: str) -> 'Password':
        """Factory method to create a Password value object"""
        return cls(value=password)

class UserClaims(BaseModel):
    """Value object for user claims in JWT tokens"""
    user_id: UUID
    email: str
    full_name: str
    roles: List[str]

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)

class TokenPair(BaseModel):
    """Value object for JWT token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds

    @field_validator('access_token', 'refresh_token')
    @classmethod
    def validate_token_format(cls, v: str) -> str:
        """Validate JWT token format"""
        if not v or not v.count('.') == 2:
            raise ValueError("Invalid token format")
        return v

    @field_validator('expires_in')
    @classmethod
    def validate_expires_in(cls, v: int) -> int:
        """Validate expiration time"""
        if v < 60:  # Minimum 1 minute
            raise ValueError("Token expiration time must be at least 60 seconds")
        if v > 86400:  # Maximum 24 hours
            raise ValueError("Token expiration time cannot exceed 24 hours")
        return v 