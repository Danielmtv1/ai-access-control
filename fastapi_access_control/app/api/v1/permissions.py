from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Optional
from uuid import UUID
from app.domain.entities.permission import Permission
from app.application.use_cases.permission_use_cases import (
    CreatePermissionUseCase, GetPermissionUseCase, ListPermissionsUseCase,
    UpdatePermissionUseCase, DeletePermissionUseCase, RevokePermissionUseCase,
    GetUserPermissionsUseCase, GetDoorPermissionsUseCase, BulkCreatePermissionsUseCase
)
from app.api.schemas.permission_schemas import (
    CreatePermissionRequest, UpdatePermissionRequest, PermissionResponse,
    PermissionListResponse, PermissionFilters, BulkPermissionRequest,
    BulkPermissionResponse, PermissionWithDetails, PermissionStatusEnum
)
from app.api.error_handlers import map_domain_error_to_http
from app.api.dependencies.auth_dependencies import get_current_active_user
from app.api.dependencies.repository_dependencies import (
    get_permission_repository, get_user_repository, get_door_repository, get_card_repository
)
from app.ports.permission_repository_port import PermissionRepositoryPort
from app.ports.user_repository_port import UserRepositoryPort
from app.ports.door_repository_port import DoorRepositoryPort
from app.ports.card_repository_port import CardRepositoryPort
from app.domain.entities.user import User
from app.config import get_settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
    dependencies=[Depends(get_current_active_user)],
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        422: {"description": "Validation Error - Invalid request data"},
        500: {"description": "Internal Server Error"}
    }
)

def _convert_to_response(permission: Permission) -> PermissionResponse:
    """Convert Permission entity to PermissionResponse"""
    # Parse access_schedule if it's a JSON string
    access_schedule = None
    if permission.access_schedule:
        try:
            access_schedule = json.loads(permission.access_schedule)
        except (json.JSONDecodeError, TypeError):
            access_schedule = None
    
    return PermissionResponse(
        id=permission.id,
        user_id=permission.user_id,
        door_id=permission.door_id,
        card_id=permission.card_id,
        status=permission.status,
        valid_from=permission.valid_from,
        valid_until=permission.valid_until,
        access_schedule=access_schedule,
        pin_required=permission.pin_required,
        created_by=permission.created_by,
        last_used=permission.last_used,
        created_at=permission.created_at,
        updated_at=permission.updated_at
    )

@router.post("/", 
             response_model=PermissionResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Create new permission",
             description="Create a new access permission for a user to access a specific door")
async def create_permission(
    request: CreatePermissionRequest,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    card_repository: CardRepositoryPort = Depends(get_card_repository)
):
    """Create a new permission"""
    try:
        use_case = CreatePermissionUseCase(
            permission_repository, user_repository, door_repository, card_repository
        )
        
        permission = await use_case.execute(
            user_id=request.user_id,
            door_id=request.door_id,
            card_id=request.card_id,
            valid_from=request.valid_from,
            valid_until=request.valid_until,
            access_schedule=request.access_schedule,
            pin_required=request.pin_required,
            created_by=current_user.id
        )
        
        return _convert_to_response(permission)
        
    except Exception as e:
        logger.error(f"Error creating permission: {e}")
        raise map_domain_error_to_http(e)

@router.get("/",
            response_model=PermissionListResponse,
            summary="List permissions",
            description="Get a paginated list of permissions with optional filters")
async def list_permissions(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    door_id: Optional[UUID] = Query(None, description="Filter by door ID"),
    card_id: Optional[UUID] = Query(None, description="Filter by card ID"),
    status: Optional[PermissionStatusEnum] = Query(None, description="Filter by status"),
    created_by: Optional[UUID] = Query(None, description="Filter by creator"),
    valid_only: Optional[bool] = Query(None, description="Show only currently valid permissions"),
    expired_only: Optional[bool] = Query(None, description="Show only expired permissions"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository)
):
    """Get a paginated list of permissions"""
    try:
        use_case = ListPermissionsUseCase(permission_repository)
        
        result = await use_case.execute(
            user_id=user_id,
            door_id=door_id,
            card_id=card_id,
            status=status.value if status else None,
            created_by=created_by,
            valid_only=valid_only,
            expired_only=expired_only,
            page=page,
            size=size
        )
        
        # Convert permissions to response format
        permission_responses = [_convert_to_response(p) for p in result["permissions"]]
        
        return PermissionListResponse(
            permissions=permission_responses,
            total=result["total"],
            page=result["page"],
            size=result["size"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"Error listing permissions: {e}")
        raise map_domain_error_to_http(e)

@router.get("/{permission_id}",
            response_model=PermissionResponse,
            summary="Get permission by ID",
            description="Retrieve a specific permission by its ID")
async def get_permission(
    permission_id: UUID,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository)
):
    """Get a permission by ID"""
    try:
        use_case = GetPermissionUseCase(permission_repository)
        permission = await use_case.execute(permission_id)
        
        return _convert_to_response(permission)
        
    except Exception as e:
        logger.error(f"Error getting permission {permission_id}: {e}")
        raise map_domain_error_to_http(e)

@router.put("/{permission_id}",
            response_model=PermissionResponse,
            summary="Update permission",
            description="Update an existing permission")
async def update_permission(
    permission_id: UUID,
    request: UpdatePermissionRequest,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository)
):
    """Update a permission"""
    try:
        use_case = UpdatePermissionUseCase(permission_repository)
        
        permission = await use_case.execute(
            permission_id=permission_id,
            status=request.status.value if request.status else None,
            valid_from=request.valid_from,
            valid_until=request.valid_until,
            access_schedule=request.access_schedule,
            pin_required=request.pin_required
        )
        
        return _convert_to_response(permission)
        
    except Exception as e:
        logger.error(f"Error updating permission {permission_id}: {e}")
        raise map_domain_error_to_http(e)

@router.delete("/{permission_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete permission",
               description="Permanently delete a permission")
async def delete_permission(
    permission_id: UUID,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository)
):
    """Delete a permission"""
    try:
        use_case = DeletePermissionUseCase(permission_repository)
        success = await use_case.execute(permission_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete permission"
            )
        
    except Exception as e:
        logger.error(f"Error deleting permission {permission_id}: {e}")
        raise map_domain_error_to_http(e)

@router.post("/{permission_id}/revoke",
             response_model=PermissionResponse,
             summary="Revoke permission",
             description="Revoke a permission by setting its status to suspended")
async def revoke_permission(
    permission_id: UUID,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository)
):
    """Revoke a permission (soft delete)"""
    try:
        use_case = RevokePermissionUseCase(permission_repository)
        permission = await use_case.execute(permission_id)
        
        return _convert_to_response(permission)
        
    except Exception as e:
        logger.error(f"Error revoking permission {permission_id}: {e}")
        raise map_domain_error_to_http(e)

@router.get("/users/{user_id}",
            response_model=List[PermissionResponse],
            summary="Get user permissions",
            description="Get all permissions for a specific user")
async def get_user_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository)
):
    """Get all permissions for a user"""
    try:
        use_case = GetUserPermissionsUseCase(permission_repository)
        permissions = await use_case.execute(user_id)
        
        return [_convert_to_response(p) for p in permissions]
        
    except Exception as e:
        logger.error(f"Error getting permissions for user {user_id}: {e}")
        raise map_domain_error_to_http(e)

@router.get("/doors/{door_id}",
            response_model=List[PermissionResponse],
            summary="Get door permissions",
            description="Get all permissions for a specific door")
async def get_door_permissions(
    door_id: UUID,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository)
):
    """Get all permissions for a door"""
    try:
        use_case = GetDoorPermissionsUseCase(permission_repository)
        permissions = await use_case.execute(door_id)
        
        return [_convert_to_response(p) for p in permissions]
        
    except Exception as e:
        logger.error(f"Error getting permissions for door {door_id}: {e}")
        raise map_domain_error_to_http(e)

@router.post("/bulk",
             response_model=BulkPermissionResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Bulk create permissions",
             description="Create multiple permissions in a single request")
async def bulk_create_permissions(
    request: BulkPermissionRequest,
    current_user: User = Depends(get_current_active_user),
    permission_repository: PermissionRepositoryPort = Depends(get_permission_repository),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    card_repository: CardRepositoryPort = Depends(get_card_repository)
):
    """Create multiple permissions in bulk"""
    try:
        use_case = BulkCreatePermissionsUseCase(
            permission_repository, user_repository, door_repository, card_repository
        )
        
        # Convert request data to dict format
        permissions_data = [p.dict() for p in request.permissions]
        
        result = await use_case.execute(permissions_data, current_user.id)
        
        # Convert created permissions to response format
        created_responses = [_convert_to_response(p) for p in result["created"]]
        
        return BulkPermissionResponse(
            created=created_responses,
            failed=result["failed"],
            total_requested=result["total_requested"],
            total_created=result["total_created"],
            total_failed=result["total_failed"]
        )
        
    except Exception as e:
        logger.error(f"Error in bulk permission creation: {e}")
        raise map_domain_error_to_http(e)