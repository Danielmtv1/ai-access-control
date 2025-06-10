from fastapi import HTTPException, status
from app.domain.errors.auth_errors import (
    AuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserInactiveError,
    InsufficientPermissionsError
)
from app.domain.exceptions import DomainError
from app.application.use_cases.card_use_cases import CardNotFoundError

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
    
    # Handle card-specific errors
    if isinstance(error, CardNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    
    # Handle general domain errors
    if isinstance(error, DomainError):
        # Check if it's a "not found" error
        error_message = str(error)
        if "not found" in error_message.lower():
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        # Check if it's a "already exists" error
        elif "already exists" in error_message.lower():
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_message
            )
        # Other domain errors as bad request
        else:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
    
    # Default error
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    ) 