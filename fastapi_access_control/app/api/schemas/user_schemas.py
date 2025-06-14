from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID

class UserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"

class RoleEnum(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"
    VIEWER = "viewer"

class CreateUserRequest(BaseModel):
    """Request model for creating a new user"""
    email: EmailStr = Field(
        ...,
        description="User email address (must be unique)",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
        example="SecurePassword123!"
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name",
        example="John Doe"
    )
    roles: List[RoleEnum] = Field(
        [RoleEnum.USER],
        description="List of user roles",
        example=[RoleEnum.USER]
    )
    status: UserStatusEnum = Field(
        UserStatusEnum.ACTIVE,
        description="User status",
        example=UserStatusEnum.ACTIVE
    )

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v):
        if not v:
            return [RoleEnum.USER]
        return list(set(v))  # Remove duplicates

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UpdateUserRequest(BaseModel):
    """Request model for updating a user"""
    full_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="User's full name",
        example="John Doe"
    )
    roles: Optional[List[RoleEnum]] = Field(
        None,
        description="List of user roles",
        example=[RoleEnum.USER, RoleEnum.OPERATOR]
    )
    status: Optional[UserStatusEnum] = Field(
        None,
        description="User status",
        example=UserStatusEnum.ACTIVE
    )

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v):
        if v is not None:
            return list(set(v))  # Remove duplicates
        return v

class ChangePasswordRequest(BaseModel):
    """Request model for changing user password"""
    current_password: str = Field(
        ...,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 characters)",
        example="NewSecurePassword123!"
    )

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserResponse(BaseModel):
    """Response model for user data"""
    id: UUID = Field(
        ...,
        description="User unique identifier",
        example="f47ac10b-58cc-4372-a567-0e02b2c3d479"
    )
    email: str = Field(
        ...,
        description="User email address",
        example="user@example.com"
    )
    full_name: str = Field(
        ...,
        description="User's full name",
        example="John Doe"
    )
    roles: List[str] = Field(
        ...,
        description="List of user roles",
        example=["user", "operator"]
    )
    status: str = Field(
        ...,
        description="User status",
        example="active"
    )
    created_at: datetime = Field(
        ...,
        description="User creation timestamp",
        example="2024-01-01T10:00:00"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
        example="2024-01-01T10:00:00"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Last login timestamp",
        example="2024-01-01T10:00:00"
    )

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, user) -> 'UserResponse':
        """Convert User entity to UserResponse"""
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=[role.value for role in user.roles],
            status=user.status.value,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login
        )

class UserListResponse(BaseModel):
    """Response model for paginated user list"""
    users: List[UserResponse] = Field(
        ...,
        description="List of users"
    )
    total: int = Field(
        ...,
        description="Total number of users",
        example=100
    )
    page: int = Field(
        ...,
        description="Current page number",
        example=1
    )
    size: int = Field(
        ...,
        description="Number of items per page",
        example=50
    )
    pages: int = Field(
        ...,
        description="Total number of pages",
        example=2
    )

class UserFilters(BaseModel):
    """Model for user filtering parameters"""
    status: Optional[UserStatusEnum] = Field(
        None,
        description="Filter by user status"
    )
    role: Optional[RoleEnum] = Field(
        None,
        description="Filter by user role"
    )
    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Search in name or email"
    )

class UserStatsResponse(BaseModel):
    """Response model for user statistics"""
    total_users: int = Field(
        ...,
        description="Total number of users",
        example=150
    )
    active_users: int = Field(
        ...,
        description="Number of active users",
        example=145
    )
    inactive_users: int = Field(
        ...,
        description="Number of inactive users",
        example=3
    )
    suspended_users: int = Field(
        ...,
        description="Number of suspended users",
        example=2
    )
    users_by_role: dict = Field(
        ...,
        description="Users count by role",
        example={"admin": 5, "operator": 20, "user": 120, "viewer": 5}
    )