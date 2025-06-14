from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import time
from ..domain.entities.permission import Permission
from uuid import UUID
class PermissionRepositoryPort(ABC):
    """Port for Permission repository operations"""
    
    @abstractmethod
    async def create(self, permission: Permission) -> Permission:
        """
        Creates a new permission entity.
        
        Args:
            permission: The permission object to be created.
        
        Returns:
            The created Permission instance.
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """
        Retrieves a permission by its unique identifier.
        
        Args:
            permission_id: The UUID of the permission to retrieve.
        
        Returns:
            The Permission object if found, otherwise None.
        """
        pass
    
    @abstractmethod
    async def get_by_user_and_door_list(self, user_id: UUID, door_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions assigned to a specific user for a given door.
        
        Args:
            user_id: Unique identifier of the user.
            door_id: Unique identifier of the door.
        
        Returns:
            A list of Permission objects associated with the user and door.
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions assigned to a specific user.
        
        Args:
            user_id: Unique identifier of the user.
        
        Returns:
            A list of Permission objects associated with the given user.
        """
        pass
    
    @abstractmethod
    async def get_by_door_id(self, door_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific door.
        
        Args:
            door_id: The unique identifier of the door.
        
        Returns:
            A list of Permission objects linked to the specified door.
        """
        pass
    
    @abstractmethod
    async def get_by_card_id(self, card_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific card.
        
        Args:
            card_id: The unique identifier of the card.
        
        Returns:
            A list of Permission objects linked to the given card.
        """
        pass
    
    @abstractmethod
    async def update(self, permission: Permission) -> Permission:
        """
        Updates an existing permission entity.
        
        Args:
            permission: The permission object with updated fields.
        
        Returns:
            The updated permission entity.
        """
        pass
    
    @abstractmethod
    async def delete(self, permission_id: UUID) -> bool:
        """
        Deletes a permission identified by its unique ID.
        
        Args:
            permission_id: The UUID of the permission to delete.
        
        Returns:
            True if the permission was successfully deleted, False otherwise.
        """
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
        """
                             Retrieves a list of permissions filtered by user, door, card, status, creator, validity, or expiration, with pagination support.
                             
                             Args:
                                 user_id: Filter by user identifier.
                                 door_id: Filter by door identifier.
                                 card_id: Filter by card identifier.
                                 status: Filter by permission status.
                                 created_by: Filter by creator identifier.
                                 valid_only: If True, include only currently valid permissions.
                                 expired_only: If True, include only expired permissions.
                                 limit: Maximum number of permissions to return.
                                 offset: Number of permissions to skip before starting to collect the result set.
                             
                             Returns:
                                 A list of permissions matching the specified filters and pagination parameters.
                             """
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
        """
                              Counts the number of permissions matching the specified filters.
                              
                              Args:
                                  user_id: Filter by user identifier.
                                  door_id: Filter by door identifier.
                                  card_id: Filter by card identifier.
                                  status: Filter by permission status.
                                  created_by: Filter by creator identifier.
                                  valid_only: If True, count only currently valid permissions.
                                  expired_only: If True, count only expired permissions.
                              
                              Returns:
                                  The number of permissions that match the provided filters.
                              """
        pass
    
    @abstractmethod
    async def get_active_permissions(self) -> List[Permission]:
        """
        Retrieves all currently active permissions.
        
        Returns:
            A list of Permission objects that are currently valid and active.
        """
        pass
    
    @abstractmethod
    async def check_access(self, user_id: UUID, door_id: UUID, current_time: time, current_day: str) -> bool:
        """
        Checks whether a user has access to a specified door at a given time and day.
        
        Args:
            user_id: Unique identifier of the user.
            door_id: Unique identifier of the door.
            current_time: The time at which access is being checked.
            current_day: The day of the week or date for access evaluation.
        
        Returns:
            True if the user has access to the door at the specified time and day, otherwise False.
        """
        pass
    
    @abstractmethod
    async def get_by_user_and_door(self, user_id: UUID, door_id: UUID) -> Optional[Permission]:
        """
        Retrieves the permission assigned to a specific user for a specific door.
        
        Args:
            user_id: Unique identifier of the user.
            door_id: Unique identifier of the door.
        
        Returns:
            The permission object if found, otherwise None.
        """
        pass