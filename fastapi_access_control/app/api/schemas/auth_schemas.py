from pydantic import BaseModel, Field
from app.domain.value_objects.auth import Email, Password, TokenPair

class TokenResponse(BaseModel):
    """Response model for token endpoints"""
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token to get new access tokens",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    token_type: str = Field(
        default="bearer",
        description="Type of token, always 'bearer' for JWT"
    )
    expires_in: int = Field(
        default=1800,
        description="Token expiration time in seconds (30 minutes)",
        example=1800
    )

    @classmethod
    def from_token_pair(cls, token_pair: TokenPair) -> 'TokenResponse':
        """Create TokenResponse from TokenPair value object"""
        return cls(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in
        )

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }

class RefreshTokenRequest(BaseModel):
    """Request model for refresh token endpoint"""
    refresh_token: str = Field(
        ...,
        description="Refresh token obtained from login endpoint",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )

    class Config:
        schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }

class LoginRequest(BaseModel):
    """Request model for login endpoint"""
    email: str = Field(
        ...,
        description="User's email address",
        example="admin@access-control.com"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="User's password (minimum 8 characters)",
        example="AdminPassword123!"
    )

    def to_domain(self) -> tuple[Email, Password]:
        """Convert request to domain value objects"""
        return (
            Email.create(self.email),
            Password.create(self.password)
        )

    class Config:
        schema_extra = {
            "example": {
                "email": "admin@access-control.com",
                "password": "AdminPassword123!"
            }
        } 