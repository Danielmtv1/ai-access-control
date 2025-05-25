from fastapi import HTTPException, status
from app.domain.errors.auth_errors import (
    AuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserInactiveError,
    InsufficientPermissionsError
)

def map_domain_error_to_http(error: Exception) -> HTTPException:
    """Map domain errors to HTTP exceptions"""
    if isinstance(error, InvalidCredentialsError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if isinstance(error, InvalidTokenError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if isinstance(error, UserInactiveError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.message
        )
    
    if isinstance(error, InsufficientPermissionsError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error.message
        )
    
    if isinstance(error, AuthError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error.message
        )
    
    # Default error
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    ) 