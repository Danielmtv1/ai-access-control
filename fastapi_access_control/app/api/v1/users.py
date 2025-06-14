from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Optional
from uuid import UUID
from app.domain.entities.user import User
from app.application.use_cases.user_use_cases import (
    CreateUserUseCase, GetUserUseCase, GetUserByEmailUseCase, ListUsersUseCase,
    UpdateUserUseCase, DeleteUserUseCase, SuspendUserUseCase, ActivateUserUseCase,
    ChangePasswordUseCase, GetUserStatsUseCase
)
from app.api.schemas.user_schemas import (
    CreateUserRequest, UpdateUserRequest, ChangePasswordRequest, UserResponse,
    UserListResponse, UserFilters, UserStatsResponse, UserStatusEnum, RoleEnum
)
from app.api.error_handlers import map_domain_error_to_http
from app.api.dependencies.auth_dependencies import get_current_active_user
from app.api.dependencies.repository_dependencies import get_user_repository
from app.ports.user_repository_port import UserRepositoryPort
from app.domain.services.auth_service import AuthService
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_active_user)],
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        422: {"description": "Validation Error - Invalid request data"},
        500: {"description": "Internal Server Error"}
    }
)

# Helper function to get auth service
def get_auth_service():
    return AuthService()

def _convert_to_response(user: User) -> UserResponse:
    """Convert User entity to UserResponse"""
    return UserResponse.from_entity(user)

@router.post("/", 
             response_model=UserResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Create new user",
             description="Create a new user account with the specified details")
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Create a new user"""
    try:
        # Check if current user has permission to create users (admin only)
        if not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create new users"
            )
        
        use_case = CreateUserUseCase(user_repository, auth_service)
        
        user = await use_case.execute(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            roles=[role.value for role in request.roles],
            status=request.status.value
        )
        
        return _convert_to_response(user)
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise map_domain_error_to_http(e)

@router.get("/",
            response_model=UserListResponse,
            summary="List users",
            description="Get a paginated list of users with optional filters")
async def list_users(
    status: Optional[UserStatusEnum] = Query(None, description="Filter by user status"),
    role: Optional[RoleEnum] = Query(None, description="Filter by user role"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search in name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Get a paginated list of users"""
    try:
        use_case = ListUsersUseCase(user_repository)
        
        result = await use_case.execute(
            status=status.value if status else None,
            role=role.value if role else None,
            search=search,
            page=page,
            size=size
        )
        
        # Convert users to response format
        user_responses = [_convert_to_response(u) for u in result["users"]]
        
        return UserListResponse(
            users=user_responses,
            total=result["total"],
            page=result["page"],
            size=result["size"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise map_domain_error_to_http(e)

@router.get("/stats",
            response_model=UserStatsResponse,
            summary="Get user statistics",
            description="Get user statistics including counts by status and role")
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Get user statistics"""
    try:
        # Check if current user has permission to view stats (admin or operator)
        if not current_user.can_manage_devices():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view user statistics"
            )
        
        use_case = GetUserStatsUseCase(user_repository)
        stats = await use_case.execute()
        
        return UserStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise map_domain_error_to_http(e)

@router.get("/{user_id}",
            response_model=UserResponse,
            summary="Get user by ID",
            description="Retrieve a specific user by their ID")
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Get a user by ID"""
    try:
        # Users can view their own profile, or admins can view any profile
        if user_id != current_user.id and not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile unless you're an admin"
            )
        
        use_case = GetUserUseCase(user_repository)
        user = await use_case.execute(user_id)
        
        return _convert_to_response(user)
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise map_domain_error_to_http(e)

@router.get("/email/{email}",
            response_model=UserResponse,
            summary="Get user by email",
            description="Retrieve a specific user by their email address")
async def get_user_by_email(
    email: str,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Get a user by email"""
    try:
        # Users can view their own profile, or admins can view any profile
        if email != current_user.email and not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own profile unless you're an admin"
            )
        
        use_case = GetUserByEmailUseCase(user_repository)
        user = await use_case.execute(email)
        
        return _convert_to_response(user)
        
    except Exception as e:
        logger.error(f"Error getting user by email {email}: {e}")
        raise map_domain_error_to_http(e)

@router.put("/{user_id}",
            response_model=UserResponse,
            summary="Update user",
            description="Update an existing user's information")
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Update a user"""
    try:
        # Users can update their own profile (limited fields), or admins can update any profile
        if user_id != current_user.id and not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own profile unless you're an admin"
            )
        
        # Non-admin users can only update their full_name
        if user_id == current_user.id and not current_user.can_access_admin_panel():
            if request.roles is not None or request.status is not None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update your full name"
                )
        
        use_case = UpdateUserUseCase(user_repository)
        
        user = await use_case.execute(
            user_id=user_id,
            full_name=request.full_name,
            roles=[role.value for role in request.roles] if request.roles else None,
            status=request.status.value if request.status else None
        )
        
        return _convert_to_response(user)
        
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise map_domain_error_to_http(e)

@router.delete("/{user_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete user",
               description="Permanently delete a user account")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Delete a user"""
    try:
        # Only admin users can delete users
        if not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can delete users"
            )
        
        # Prevent users from deleting themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account"
            )
        
        use_case = DeleteUserUseCase(user_repository)
        success = await use_case.execute(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise map_domain_error_to_http(e)

@router.post("/{user_id}/suspend",
             response_model=UserResponse,
             summary="Suspend user",
             description="Suspend a user account (soft delete)")
async def suspend_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Suspend a user account"""
    try:
        # Only admin users can suspend users
        if not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can suspend users"
            )
        
        # Prevent users from suspending themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot suspend your own account"
            )
        
        use_case = SuspendUserUseCase(user_repository)
        user = await use_case.execute(user_id)
        
        return _convert_to_response(user)
        
    except Exception as e:
        logger.error(f"Error suspending user {user_id}: {e}")
        raise map_domain_error_to_http(e)

@router.post("/{user_id}/activate",
             response_model=UserResponse,
             summary="Activate user",
             description="Activate a suspended or inactive user account")
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Activate a user account"""
    try:
        # Only admin users can activate users
        if not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can activate users"
            )
        
        use_case = ActivateUserUseCase(user_repository)
        user = await use_case.execute(user_id)
        
        return _convert_to_response(user)
        
    except Exception as e:
        logger.error(f"Error activating user {user_id}: {e}")
        raise map_domain_error_to_http(e)

@router.post("/{user_id}/change-password",
             response_model=UserResponse,
             summary="Change user password",
             description="Change a user's password")
async def change_password(
    user_id: UUID,
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        # Users can change their own password, or admins can change any password
        if user_id != current_user.id and not current_user.can_access_admin_panel():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only change your own password unless you're an admin"
            )
        
        use_case = ChangePasswordUseCase(user_repository, auth_service)
        
        user = await use_case.execute(
            user_id=user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        return _convert_to_response(user)
        
    except Exception as e:
        logger.error(f"Error changing password for user {user_id}: {e}")
        raise map_domain_error_to_http(e)