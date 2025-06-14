from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from ..domain.entities.user import User

class UserRepositoryPort(ABC):
    """Port for User repository operations"""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Asynchronously creates a new user and returns the created user entity.
        
        Args:
            user: The user entity to be created.
        
        Returns:
            The newly created user entity.
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Asynchronously retrieves a user by their unique identifier.
        
        Args:
            user_id: The UUID of the user to retrieve.
        
        Returns:
            The user entity if found, or None if no user exists with the given ID.
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Asynchronously updates an existing user entity.
        
        Args:
        	user: The user entity with updated information.
        
        Returns:
        	The updated user entity.
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """
        Asynchronously deletes a user by their unique identifier.
        
        Args:
            user_id: The UUID of the user to delete.
        
        Returns:
            True if the user was successfully deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    async def list_users(self, 
                        status: Optional[str] = None,
                        role: Optional[str] = None,
                        search: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[User]:
        """
                        Retrieves a list of users filtered by status, role, and search criteria, with pagination.
                        
                        Args:
                            status: Optional user status to filter by.
                            role: Optional user role to filter by.
                            search: Optional search term to match against user attributes.
                            limit: Maximum number of users to return.
                            offset: Number of users to skip before starting to collect the result set.
                        
                        Returns:
                            A list of users matching the specified filters and pagination parameters.
                        """
        pass
    
    @abstractmethod
    async def count_users(self,
                         status: Optional[str] = None,
                         role: Optional[str] = None,
                         search: Optional[str] = None) -> int:
        """
                         Counts the number of users matching optional status, role, and search filters.
                         
                         Args:
                             status: Optional user status to filter by.
                             role: Optional user role to filter by.
                             search: Optional search term to filter users.
                         
                         Returns:
                             The count of users matching the specified filters.
                         """
        pass 