from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from ..domain.entities.user import User

class UserRepositoryPort(ABC):
    """Port for User repository operations"""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update existing user"""
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID"""
        pass
    
    @abstractmethod
    async def list_users(self, 
                        status: Optional[str] = None,
                        role: Optional[str] = None,
                        search: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[User]:
        """List users with filters and pagination"""
        pass
    
    @abstractmethod
    async def count_users(self,
                         status: Optional[str] = None,
                         role: Optional[str] = None,
                         search: Optional[str] = None) -> int:
        """Count users matching filters"""
        pass 