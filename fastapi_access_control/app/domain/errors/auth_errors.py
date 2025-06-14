from dataclasses import dataclass
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class AuthError(Exception):
    """Base class for authentication errors"""
    message: str
    code: str
    details: Optional[dict] = None

@dataclass(frozen=True)
class InvalidCredentialsError(AuthError):
    """Error when credentials are invalid"""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            code="INVALID_CREDENTIALS"
        )

@dataclass(frozen=True)
class InvalidTokenError(AuthError):
    """Error when token is invalid or expired"""
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(
            message=message,
            code="INVALID_TOKEN"
        )

@dataclass(frozen=True)
class UserInactiveError(AuthError):
    """Error when user account is inactive"""
    def __init__(self, user_id: UUID):
        """
        Initializes a UserInactiveError for an inactive user account.
        
        Args:
            user_id: The UUID of the inactive user.
        """
        super().__init__(
            message=f"User {user_id} is inactive",
            code="USER_INACTIVE",
            details={"user_id": user_id}
        )

@dataclass(frozen=True)
class InsufficientPermissionsError(AuthError):
    """Error when user lacks required permissions"""
    def __init__(self, required_roles: list[str]):
        super().__init__(
            message="Insufficient permissions",
            code="INSUFFICIENT_PERMISSIONS",
            details={"required_roles": required_roles}
        ) 