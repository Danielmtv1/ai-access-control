from abc import ABC, abstractmethod
from typing import Optional, List
from ..domain.entities.permission import Permission

class PermissionRepositoryPort(ABC):
    """Port for Permission repository operations"""
    
    @abstractmethod
    async def create(self, permission: Permission) -> Permission:
        """Create a new permission"""
        pass
    
    @abstractmethod
    async def get_by_id(self, permission_id: int) -> Optional[Permission]:
        """Get permission by ID"""
        pass
    
    @abstractmethod
    async def get_by_user_and_door(self, user_id: int, door_id: int) -> List[Permission]:
        """Get permissions for user and door"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> List[Permission]:
        """Get all permissions for a user"""
        pass
    
    @abstractmethod
    async def get_by_door_id(self, door_id: int) -> List[Permission]:
        """Get all permissions for a door"""
        pass
    
    @abstractmethod
    async def get_by_card_id(self, card_id: int) -> List[Permission]:
        """Get all permissions for a card"""
        pass
    
    @abstractmethod
    async def update(self, permission: Permission) -> Permission:
        """Update existing permission"""
        pass
    
    @abstractmethod
    async def delete(self, permission_id: int) -> bool:
        """Delete permission by ID"""
        pass
    
    @abstractmethod
    async def list_permissions(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        """List permissions with pagination"""
        pass
    
    @abstractmethod
    async def get_active_permissions(self) -> List[Permission]:
        """Get all active permissions"""
        pass
    
    @abstractmethod
    async def check_access(self, user_id: int, door_id: int, card_id: Optional[int] = None) -> Optional[Permission]:
        """Check if user has access to door (optionally with specific card)"""
        pass