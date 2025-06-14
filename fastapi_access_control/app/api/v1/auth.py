from fastapi import APIRouter, Depends, HTTPException, status, Body, Form
from fastapi.security import OAuth2PasswordRequestForm
from app.domain.entities.user import User
from app.domain.services.auth_service import AuthService
from app.application.use_cases.auth_use_cases import AuthenticateUserUseCase, RefreshTokenUseCase
from app.api.schemas.auth_schemas import TokenResponse, RefreshTokenRequest, LoginRequest
from app.api.error_handlers import map_domain_error_to_http
from app.api.dependencies.repository_dependencies import get_user_repository
from app.ports.user_repository_port import UserRepositoryPort
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
    user_repository: UserRepositoryPort = Depends(get_user_repository)
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
    user_repository: UserRepositoryPort = Depends(get_user_repository)
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

@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 Token Endpoint",
    description="""
    OAuth2 compatible token endpoint for Swagger UI authentication.
    
    This endpoint accepts form data and is compatible with the OAuth2 password flow.
    It provides the same functionality as the /login endpoint but with form-based input
    that works with the "Authorize" button in Swagger UI.
    
    **Form Parameters:**
    - username: User's email address
    - password: User's password
    - grant_type: Must be "password" (automatically handled)
    """,
    responses={
        200: {
            "description": "Successful authentication",
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
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """
    OAuth2 compatible token endpoint for authentication.
    
    This endpoint accepts form data and provides the same authentication
    functionality as the /login endpoint, but in a format compatible
    with OAuth2 and Swagger UI.
    
    Args:
        form_data: OAuth2 form data with username (email) and password
        auth_service: Authentication service instance
        user_repository: User repository instance
    
    Returns:
        TokenResponse: JWT tokens for authentication
        
    Raises:
        HTTPException: If credentials are invalid or user is inactive
    """
    try:
        # Use username field as email (OAuth2 standard)
        email = form_data.username
        password = form_data.password
        
        logger.info(f"Token endpoint login attempt for email: {email}")
        
        authenticate_use_case = AuthenticateUserUseCase(
            auth_service=auth_service,
            user_repository=user_repository
        )
        
        tokens = await authenticate_use_case.execute(email, password)
        
        logger.info(f"Successful token endpoint login for email: {email}")
        return TokenResponse.from_token_pair(tokens)
        
    except ValueError as e:
        logger.error(f"Validation error for email {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except InvalidCredentialsError as e:
        logger.error(f"Invalid credentials for email {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token endpoint error for email {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        ) 