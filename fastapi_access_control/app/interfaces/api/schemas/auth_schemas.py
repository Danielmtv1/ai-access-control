from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str = Field(..., min_length=6)

class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfo"

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str

class UserCreateRequest(BaseModel):
    """Schema for user creation request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    roles: Optional[List[str]] = None

class UserInfo(BaseModel):
    """Schema for user information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    full_name: str
    roles: List[str]
    status: str
    created_at: datetime
    last_login: Optional[datetime] = None

class UserResponse(BaseModel):
    """Schema for user response"""
    user: UserInfo
    message: str = "User retrieved successfully"

class UsersListResponse(BaseModel):
    """Schema for users list response"""
    users: List[UserInfo]
    total: int
    skip: int
    limit: int

# Update forward references
LoginResponse.model_rebuild() 