from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from typing import List
import logging

from app.interfaces.api.schemas.auth_schemas import (
    LoginRequest, LoginResponse, RefreshTokenRequest, 
    UserCreateRequest, UserResponse, UserInfo, UsersListResponse
)
from app.interfaces.api.dependencies.auth_dependencies import (
    get_auth_service, get_user_repository, get_current_user, 
    get_current_user_claims, require_admin, require_viewer, security
)
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims
from app.domain.entities.user import User
from ....ports.user_repository_port import UserRepositoryPort
from ....application.use_cases.auth_use_cases import (
    AuthenticateUserUseCase, RefreshTokenUseCase, CreateUserUseCase,
    AuthenticationError
)
from ....domain.exceptions import DomainError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

async def log_user_activity(user_id: int | None, activity_type: str, message: str):
    """Log user activity asynchronously"""
    try:
        # TODO: Implement proper activity logging
        # This could be:
        # - Store in database
        # - Send to logging service
        # - Write to audit log
        logger.info(f"User Activity - Type: {activity_type}, User: {user_id}, Message: {message}")
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    background_tasks: BackgroundTasks,
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return JWT tokens
    
    - **email**: User email address
    - **password**: User password
    
    Returns access_token and refresh_token
    """
    try:
        # Execute authentication use case
        use_case = AuthenticateUserUseCase(user_repository, auth_service)
        token_pair = await use_case.execute(login_data.email, login_data.password)
        
        # Get user info for response
        user = await user_repository.get_by_email(login_data.email)
        
        # Log successful login in background
        background_tasks.add_task(
            log_user_activity, 
            user.id, 
            "login_success",
            f"User {user.email} logged in successfully"
        )
        
        return LoginResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            user=UserInfo(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                roles=[role.value for role in user.roles],
                status=user.status.value,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
        
    except AuthenticationError as e:
        # Log failed login attempt in background
        background_tasks.add_task(
            log_user_activity,
            None,
            "login_failed", 
            f"Failed login attempt for {login_data.email}: {str(e)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access_token and refresh_token pair
    """
    try:
        use_case = RefreshTokenUseCase(user_repository, auth_service)
        token_pair = await use_case.execute(refresh_data.refresh_token)
        
        # Get user info for response
        payload = auth_service.decode_token(refresh_data.refresh_token)
        user = await user_repository.get_by_id(int(payload["sub"]))
        
        return LoginResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type=token_pair.token_type,
            expires_in=token_pair.expires_in,
            user=UserInfo(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                roles=[role.value for role in user.roles],
                status=user.status.value,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header
    """
    return UserResponse(
        user=UserInfo(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            roles=[role.value for role in current_user.roles],
            status=current_user.status.value,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
    )

@router.post("/logout")
async def logout(
    background_tasks: BackgroundTasks,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    claims: UserClaims = Depends(get_current_user_claims)
):
    """
    Logout user (token invalidation would be handled by client)
    
    In a production environment, you might want to:
    - Add token to blacklist
    - Store in Redis with TTL
    - Invalidate refresh tokens
    """
    # Log logout activity
    background_tasks.add_task(
        log_user_activity,
        claims.user_id,
        "logout",
        f"User {claims.email} logged out"
    ) 