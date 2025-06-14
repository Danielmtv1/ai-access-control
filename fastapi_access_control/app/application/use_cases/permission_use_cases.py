from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, UTC
from uuid import UUID
from ...domain.entities.permission import Permission
from ...ports.permission_repository_port import PermissionRepositoryPort
from ...ports.user_repository_port import UserRepositoryPort
from ...ports.door_repository_port import DoorRepositoryPort
from ...ports.card_repository_port import CardRepositoryPort
from ...domain.exceptions import (
    DomainError, PermissionNotFoundError, UserNotFoundError, 
    DoorNotFoundError, CardNotFoundError, EntityAlreadyExistsError
)
import logging
import json

logger = logging.getLogger(__name__)

class CreatePermissionUseCase:
    """Use case for creating new permissions"""
    
    def __init__(self, 
                 permission_repository: PermissionRepositoryPort,
                 user_repository: UserRepositoryPort,
                 door_repository: DoorRepositoryPort,
                 card_repository: Optional[CardRepositoryPort] = None):
        self.permission_repository = permission_repository
        self.user_repository = user_repository
        self.door_repository = door_repository
        self.card_repository = card_repository
    
    async def execute(self,
                     user_id: UUID,
                     door_id: UUID,
                     created_by: UUID,
                     card_id: Optional[UUID] = None,
                     valid_from: Optional[datetime] = None,
                     valid_until: Optional[datetime] = None,
                     access_schedule: Optional[Dict[str, Any]] = None,
                     pin_required: bool = False) -> Permission:
        """Create new permission"""
        logger.info(f"Creating permission for user {user_id} on door {door_id}")
        
        # Validate user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Validate door exists
        door = await self.door_repository.get_by_id(door_id)
        if not door:
            raise DoorNotFoundError(f"Door with ID {door_id} not found")
        
        # Validate card if provided
        if card_id and self.card_repository:
            card = await self.card_repository.get_by_id(card_id)
            if not card:
                raise CardNotFoundError(f"Card with ID {card_id} not found")
        
        # Check if permission already exists
        existing_permissions = await self.permission_repository.get_by_user_and_door_list(user_id, door_id)
        active_permissions = [p for p in existing_permissions if p.status == "active"]
        if active_permissions:
            raise EntityAlreadyExistsError(f"Active permission already exists for user {user_id} on door {door_id}")
        
        # Set default valid_from if not provided
        if not valid_from:
            valid_from = datetime.now(UTC)
        
        # Convert access_schedule to JSON string if provided
        schedule_str = None
        if access_schedule:
            schedule_str = json.dumps(access_schedule)
        
        # Create permission entity
        permission = Permission(
            user_id=user_id,
            door_id=door_id,
            card_id=card_id,
            valid_from=valid_from,
            valid_until=valid_until,
            access_schedule=schedule_str,
            pin_required=pin_required,
            created_by=created_by,
            status="active"
        )
        
        # Save to repository
        created_permission = await self.permission_repository.create(permission)
        logger.info(f"Permission created successfully with ID {created_permission.id}")
        
        return created_permission

class GetPermissionUseCase:
    """Use case for retrieving permission by ID"""
    
    def __init__(self, permission_repository: PermissionRepositoryPort):
        self.permission_repository = permission_repository
    
    async def execute(self, permission_id: UUID) -> Permission:
        """Get permission by ID"""
        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(f"Permission with ID {permission_id} not found")
        
        return permission

class ListPermissionsUseCase:
    """Use case for listing permissions with filters and pagination"""
    
    def __init__(self, permission_repository: PermissionRepositoryPort):
        self.permission_repository = permission_repository
    
    async def execute(self,
                     user_id: Optional[UUID] = None,
                     door_id: Optional[UUID] = None,
                     card_id: Optional[UUID] = None,
                     status: Optional[str] = None,
                     created_by: Optional[UUID] = None,
                     valid_only: Optional[bool] = None,
                     expired_only: Optional[bool] = None,
                     page: int = 1,
                     size: int = 50) -> Dict[str, Any]:
        """List permissions with filters"""
        logger.info(f"Listing permissions with filters: user_id={user_id}, door_id={door_id}")
        
        # Calculate offset
        offset = (page - 1) * size
        
        # Get permissions based on filters
        permissions = await self.permission_repository.list_permissions(
            user_id=user_id,
            door_id=door_id,
            card_id=card_id,
            status=status,
            created_by=created_by,
            valid_only=valid_only,
            expired_only=expired_only,
            limit=size,
            offset=offset
        )
        
        # Get total count
        total = await self.permission_repository.count_permissions(
            user_id=user_id,
            door_id=door_id,
            card_id=card_id,
            status=status,
            created_by=created_by,
            valid_only=valid_only,
            expired_only=expired_only
        )
        
        # Calculate pagination info
        pages = (total + size - 1) // size
        
        return {
            "permissions": permissions,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }

class UpdatePermissionUseCase:
    """Use case for updating permissions"""
    
    def __init__(self, permission_repository: PermissionRepositoryPort):
        self.permission_repository = permission_repository
    
    async def execute(self,
                     permission_id: UUID,
                     status: Optional[str] = None,
                     valid_from: Optional[datetime] = None,
                     valid_until: Optional[datetime] = None,
                     access_schedule: Optional[Dict[str, Any]] = None,
                     pin_required: Optional[bool] = None) -> Permission:
        """Update permission"""
        logger.info(f"Updating permission {permission_id}")
        
        # Get existing permission
        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(f"Permission with ID {permission_id} not found")
        
        # Update fields if provided
        if status is not None:
            permission.status = status
        if valid_from is not None:
            permission.valid_from = valid_from
        if valid_until is not None:
            permission.valid_until = valid_until
        if access_schedule is not None:
            permission.access_schedule = json.dumps(access_schedule)
        if pin_required is not None:
            permission.pin_required = pin_required
        
        # Update timestamp
        permission.updated_at = datetime.now(UTC)
        
        # Save changes
        updated_permission = await self.permission_repository.update(permission)
        logger.info(f"Permission {permission_id} updated successfully")
        
        return updated_permission

class DeletePermissionUseCase:
    """Use case for deleting permissions"""
    
    def __init__(self, permission_repository: PermissionRepositoryPort):
        self.permission_repository = permission_repository
    
    async def execute(self, permission_id: UUID) -> bool:
        """Delete permission"""
        logger.info(f"Deleting permission {permission_id}")
        
        # Check if permission exists
        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(f"Permission with ID {permission_id} not found")
        
        # Delete permission
        success = await self.permission_repository.delete(permission_id)
        if success:
            logger.info(f"Permission {permission_id} deleted successfully")
        else:
            logger.error(f"Failed to delete permission {permission_id}")
        
        return success

class RevokePermissionUseCase:
    """Use case for revoking permissions (soft delete by setting status)"""
    
    def __init__(self, permission_repository: PermissionRepositoryPort):
        self.permission_repository = permission_repository
    
    async def execute(self, permission_id: UUID) -> Permission:
        """Revoke permission by setting status to suspended"""
        logger.info(f"Revoking permission {permission_id}")
        
        # Get existing permission
        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise PermissionNotFoundError(f"Permission with ID {permission_id} not found")
        
        # Set status to suspended
        permission.status = "suspended"
        permission.updated_at = datetime.now(UTC)
        
        # Save changes
        updated_permission = await self.permission_repository.update(permission)
        logger.info(f"Permission {permission_id} revoked successfully")
        
        return updated_permission

class GetUserPermissionsUseCase:
    """Use case for getting all permissions for a specific user"""
    
    def __init__(self, permission_repository: PermissionRepositoryPort):
        self.permission_repository = permission_repository
    
    async def execute(self, user_id: UUID) -> List[Permission]:
        """Get all permissions for a user"""
        logger.info(f"Getting permissions for user {user_id}")
        
        permissions = await self.permission_repository.get_by_user_id(user_id)
        logger.info(f"Found {len(permissions)} permissions for user {user_id}")
        
        return permissions

class GetDoorPermissionsUseCase:
    """Use case for getting all permissions for a specific door"""
    
    def __init__(self, permission_repository: PermissionRepositoryPort):
        self.permission_repository = permission_repository
    
    async def execute(self, door_id: UUID) -> List[Permission]:
        """Get all permissions for a door"""
        logger.info(f"Getting permissions for door {door_id}")
        
        permissions = await self.permission_repository.get_by_door_id(door_id)
        logger.info(f"Found {len(permissions)} permissions for door {door_id}")
        
        return permissions

class BulkCreatePermissionsUseCase:
    """Use case for creating multiple permissions in batch"""
    
    def __init__(self, 
                 permission_repository: PermissionRepositoryPort,
                 user_repository: UserRepositoryPort,
                 door_repository: DoorRepositoryPort,
                 card_repository: Optional[CardRepositoryPort] = None):
        self.permission_repository = permission_repository
        self.user_repository = user_repository
        self.door_repository = door_repository
        self.card_repository = card_repository
    
    async def execute(self, 
                     permissions_data: List[Dict[str, Any]], 
                     created_by: UUID) -> Dict[str, Any]:
        """Create multiple permissions"""
        logger.info(f"Creating {len(permissions_data)} permissions in bulk")
        
        created = []
        failed = []
        
        for i, data in enumerate(permissions_data):
            try:
                # Create individual permission
                create_use_case = CreatePermissionUseCase(
                    self.permission_repository,
                    self.user_repository,
                    self.door_repository,
                    self.card_repository
                )
                
                permission = await create_use_case.execute(
                    user_id=data.get('user_id'),
                    door_id=data.get('door_id'),
                    card_id=data.get('card_id'),
                    valid_from=data.get('valid_from'),
                    valid_until=data.get('valid_until'),
                    access_schedule=data.get('access_schedule'),
                    pin_required=data.get('pin_required', False),
                    created_by=created_by
                )
                created.append(permission)
                
            except Exception as e:
                failed.append({
                    "index": i,
                    "data": data,
                    "error": str(e)
                })
                logger.error(f"Failed to create permission at index {i}: {e}")
        
        result = {
            "created": created,
            "failed": failed,
            "total_requested": len(permissions_data),
            "total_created": len(created),
            "total_failed": len(failed)
        }
        
        logger.info(f"Bulk creation completed: {len(created)} created, {len(failed)} failed")
        return result