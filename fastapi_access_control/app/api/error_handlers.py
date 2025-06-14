from fastapi import HTTPException, status
from app.domain.errors.auth_errors import (
    AuthError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserInactiveError,
    InsufficientPermissionsError
)
from app.domain.exceptions import (
    DomainError,
    EntityNotFoundError,
    CardNotFoundError,
    DoorNotFoundError,
    UserNotFoundError,
    PermissionNotFoundError,
    EntityAlreadyExistsError,
    InvalidCardError,
    InvalidDoorError,
    AccessDeniedError,
    InvalidPinError
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
    
    # Handle Entity Not Found errors with unified hierarchy
    if isinstance(error, EntityNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    
    # Handle Entity Already Exists errors
    if isinstance(error, EntityAlreadyExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )
    
    # Handle Access Control errors
    if isinstance(error, AccessDeniedError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error)
        )
    
    if isinstance(error, (InvalidCardError, InvalidDoorError, InvalidPinError)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    
    # Handle general domain errors
    if isinstance(error, DomainError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
    
    # Default error
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    ) 