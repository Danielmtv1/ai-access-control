from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.domain.entities.user import User
from app.domain.services.auth_service import AuthService
from app.infrastructure.persistence.adapters.user_repository import SqlAlchemyUserRepository
from app.shared.database import AsyncSessionLocal
from app.application.use_cases.auth_use_cases import AuthenticateUserUseCase, RefreshTokenUseCase
from app.api.schemas.auth_schemas import TokenResponse, RefreshTokenRequest, LoginRequest
from app.api.error_handlers import map_domain_error_to_http
from app.domain.errors.auth_errors import InvalidCredentialsError, InvalidTokenError
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized - Invalid credentials"},
        422: {"description": "Validation Error - Invalid request data"},
        500: {"description": "Internal Server Error"}
    }
)

def get_auth_service():
    """Dependency to get AuthService instance"""
    return AuthService()

def get_user_repository():
    """Dependency to get UserRepository instance"""
    return SqlAlchemyUserRepository(session_factory=AsyncSessionLocal)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="""
    Authenticate a user and return JWT tokens.
    
    This endpoint validates user credentials and returns:
    - Access token: Short-lived token for API access
    - Refresh token: Long-lived token to get new access tokens
    - Token type: Always "bearer"
    - Expiration time: In seconds
    
    The access token should be included in the Authorization header for protected endpoints:
    ```
    Authorization: Bearer <access_token>
    ```
    """,
    responses={
        200: {
            "description": "Successful login",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid email or password"
                    }
                }
            }
        }
    }
)
async def login(
    login_data: LoginRequest = Body(
        ...,
        example={
            "email": "admin@access-control.com",
            "password": "AdminPassword123!"
        },
        description="User credentials"
    ),
    auth_service: AuthService = Depends(get_auth_service),
    user_repository: SqlAlchemyUserRepository = Depends(get_user_repository)
):
    """
    Authenticate a user and return JWT tokens.
    
    Args:
        login_data: User credentials (email and password)
        auth_service: Authentication service instance
        user_repository: User repository instance
    
    Returns:
        TokenResponse: JWT tokens for authentication
        
    Raises:
        HTTPException: If credentials are invalid or user is inactive
    """
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        
        # Convert request to domain value objects
        email, password = login_data.to_domain()
        
        authenticate_use_case = AuthenticateUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        tokens = await authenticate_use_case.execute(str(email), str(password))
        
        logger.info(f"Successful login for email: {login_data.email}")
        return TokenResponse.from_token_pair(tokens)
        
    except ValueError as e:
        logger.error(f"Validation error for email {login_data.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except InvalidCredentialsError as e:
        logger.error(f"Invalid credentials for email {login_data.email}")
        raise map_domain_error_to_http(e)
    except Exception as e:
        logger.error(f"Login error for email {login_data.email}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
    description="""
    Get a new access token using a refresh token.
    
    This endpoint is used to get a new access token when the current one expires.
    The refresh token should be obtained from the login endpoint.
    
    The new access token should be used to replace the expired one in the Authorization header.
    """,
    responses={
        200: {
            "description": "Token refreshed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer",
                        "expires_in": 1800
                    }
                }
            }
        },
        401: {
            "description": "Invalid refresh token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid refresh token"
                    }
                }
            }
        }
    }
)
async def refresh_token(
    refresh_request: RefreshTokenRequest = Body(
        ...,
        example={
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
        },
        description="Refresh token from previous login"
    ),
    auth_service: AuthService = Depends(get_auth_service),
    user_repository: SqlAlchemyUserRepository = Depends(get_user_repository)
):
    """
    Refresh the access token using a refresh token.
    
    Args:
        refresh_request: Refresh token from previous login
        auth_service: Authentication service instance
        user_repository: User repository instance
    
    Returns:
        TokenResponse: New JWT tokens
        
    Raises:
        HTTPException: If refresh token is invalid or user is inactive
    """
    try:
        refresh_use_case = RefreshTokenUseCase(auth_service, user_repository)
        tokens = await refresh_use_case.execute(refresh_request.refresh_token)
        return TokenResponse.from_token_pair(tokens)
    except InvalidTokenError as e:
        logger.error(f"Invalid refresh token: {str(e)}")
        raise map_domain_error_to_http(e)
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}")
        raise map_domain_error_to_http(e) 