from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List
from uuid import UUID
import re
from ...config import get_settings

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
        """
        Validates password strength according to configurable application settings.
        
        Checks that the password meets minimum length and character composition requirements
        (uppercase, lowercase, digits, special characters) as specified in the current settings.
        Raises a ValueError if any requirement is not satisfied.
        
        Args:
            v: The password string to validate.
        
        Returns:
            The validated password string.
        
        Raises:
            ValueError: If the password does not meet the configured strength requirements.
        """
        settings = get_settings()
        
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
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
    expires_in: int = Field(default_factory=lambda: get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60)

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
        """
        Validates that the token expiration time is within the configured minimum and maximum bounds.
        
        Raises:
            ValueError: If the expiration time is less than the minimum or greater than the maximum allowed.
            
        Returns:
            The validated expiration time in seconds.
        """
        settings = get_settings()
        if v < settings.TOKEN_MIN_EXPIRE_SECONDS:
            raise ValueError(f"Token expiration time must be at least {settings.TOKEN_MIN_EXPIRE_SECONDS} seconds")
        if v > settings.TOKEN_MAX_EXPIRE_SECONDS:
            raise ValueError(f"Token expiration time cannot exceed {settings.TOKEN_MAX_EXPIRE_SECONDS} seconds")
        return v 