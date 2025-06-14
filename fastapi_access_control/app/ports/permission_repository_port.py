from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import time
from ..domain.entities.permission import Permission
from uuid import UUID
class PermissionRepositoryPort(ABC):
    """Port for Permission repository operations"""
    
    @abstractmethod
    async def create(self, permission: Permission) -> Permission:
        """Create a new permission"""
        pass
    
    @abstractmethod
    async def get_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """Get permission by ID"""
        pass
    
    @abstractmethod
    async def get_by_user_and_door_list(self, user_id: UUID, door_id: UUID) -> List[Permission]:
        """Get permissions for user and door"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[Permission]:
        """Get all permissions for a user"""
        pass
    
    @abstractmethod
    async def get_by_door_id(self, door_id: UUID) -> List[Permission]:
        """Get all permissions for a door"""
        pass
    
    @abstractmethod
    async def get_by_card_id(self, card_id: UUID) -> List[Permission]:
        """Get all permissions for a card"""
        pass
    
    @abstractmethod
    async def update(self, permission: Permission) -> Permission:
        """Update existing permission"""
        pass
    
    @abstractmethod
    async def delete(self, permission_id: UUID) -> bool:
        """Delete permission by ID"""
        pass
    
    @abstractmethod
    async def list_permissions(self, 
                             user_id: Optional[UUID] = None,
                             door_id: Optional[UUID] = None,
                             card_id: Optional[UUID] = None,
                             status: Optional[str] = None,
                             created_by: Optional[UUID] = None,
                             valid_only: Optional[bool] = None,
                             expired_only: Optional[bool] = None,
                             limit: int = 100,
                             offset: int = 0) -> List[Permission]:
        """List permissions with filters and pagination"""
        pass
    
    @abstractmethod
    async def count_permissions(self,
                              user_id: Optional[UUID] = None,
                              door_id: Optional[UUID] = None,
                              card_id: Optional[UUID] = None,
                              status: Optional[str] = None,
                              created_by: Optional[UUID] = None,
                              valid_only: Optional[bool] = None,
                              expired_only: Optional[bool] = None) -> int:
        """Count permissions matching filters"""
        pass
    
    @abstractmethod
    async def get_active_permissions(self) -> List[Permission]:
        """Get all active permissions"""
        pass
    
    @abstractmethod
    async def check_access(self, user_id: UUID, door_id: UUID, current_time: time, current_day: str) -> bool:
        """Check if user has access to door at the given time and day"""
        pass
    
    @abstractmethod
    async def get_by_user_and_door(self, user_id: UUID, door_id: UUID) -> Optional[Permission]:
        """Get permission for specific user and door combination"""
        pass