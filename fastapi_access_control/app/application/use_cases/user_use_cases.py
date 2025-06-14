from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, UTC
from uuid import UUID
from ...domain.entities.user import User, Role, UserStatus
from ...domain.services.auth_service import AuthService
from ...ports.user_repository_port import UserRepositoryPort
from ...domain.exceptions import (
    DomainError, UserNotFoundError, EntityAlreadyExistsError, ValidationError
)
import logging

logger = logging.getLogger(__name__)

class CreateUserUseCase:
    """Use case for creating new users"""
    
    def __init__(self, 
                 user_repository: UserRepositoryPort,
                 auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self,
                     email: str,
                     password: str,
                     full_name: str,
                     roles: List[str],
                     status: str = "active") -> User:
        """Create new user"""
        logger.info(f"Creating user with email: {email}")
        
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise EntityAlreadyExistsError(f"User with email {email} already exists")
        
        # Hash password
        hashed_password = self.auth_service.hash_password(password)
        
        # Convert roles to Role enum
        user_roles = []
        for role_str in roles:
            try:
                user_roles.append(Role(role_str))
            except ValueError:
                raise ValidationError(f"Invalid role: {role_str}")
        
        # Convert status to UserStatus enum
        try:
            user_status = UserStatus(status)
        except ValueError:
            raise ValidationError(f"Invalid status: {status}")
        
        # Create user entity
        now = datetime.now(UTC)
        user = User(
            id=None,  # Will be set by repository
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            roles=user_roles,
            status=user_status,
            created_at=now,
            updated_at=now,
            last_login=None
        )
        
        # Save to repository
        created_user = await self.user_repository.create(user)
        logger.info(f"User created successfully with ID {created_user.id}")
        
        return created_user

class GetUserUseCase:
    """Use case for retrieving user by ID"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> User:
        """Get user by ID"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return user

class GetUserByEmailUseCase:
    """Use case for retrieving user by email"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self, email: str) -> User:
        """Get user by email"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")
        
        return user

class ListUsersUseCase:
    """Use case for listing users with filters and pagination"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self,
                     status: Optional[str] = None,
                     role: Optional[str] = None,
                     search: Optional[str] = None,
                     page: int = 1,
                     size: int = 50) -> Dict[str, Any]:
        """List users with filters"""
        logger.info(f"Listing users with filters: status={status}, role={role}, search={search}")
        
        # Calculate offset
        offset = (page - 1) * size
        
        # Get users based on filters
        users = await self.user_repository.list_users(
            status=status,
            role=role,
            search=search,
            limit=size,
            offset=offset
        )
        
        # Get total count
        total = await self.user_repository.count_users(
            status=status,
            role=role,
            search=search
        )
        
        # Calculate pagination info
        pages = (total + size - 1) // size
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }

class UpdateUserUseCase:
    """Use case for updating users"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self,
                     user_id: UUID,
                     full_name: Optional[str] = None,
                     roles: Optional[List[str]] = None,
                     status: Optional[str] = None) -> User:
        """Update user"""
        logger.info(f"Updating user {user_id}")
        
        # Get existing user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Update fields if provided
        if full_name is not None:
            user.full_name = full_name
        
        if roles is not None:
            # Convert roles to Role enum
            user_roles = []
            for role_str in roles:
                try:
                    user_roles.append(Role(role_str))
                except ValueError:
                    raise ValidationError(f"Invalid role: {role_str}")
            user.roles = user_roles
        
        if status is not None:
            # Convert status to UserStatus enum
            try:
                user.status = UserStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid status: {status}")
        
        # Update timestamp
        user.updated_at = datetime.now(UTC)
        
        # Save changes
        updated_user = await self.user_repository.update(user)
        logger.info(f"User {user_id} updated successfully")
        
        return updated_user

class DeleteUserUseCase:
    """Use case for deleting users"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> bool:
        """Delete user"""
        logger.info(f"Deleting user {user_id}")
        
        # Check if user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Delete user
        success = await self.user_repository.delete(user_id)
        if success:
            logger.info(f"User {user_id} deleted successfully")
        else:
            logger.error(f"Failed to delete user {user_id}")
        
        return success

class SuspendUserUseCase:
    """Use case for suspending users (soft delete by setting status)"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> User:
        """Suspend user by setting status to suspended"""
        logger.info(f"Suspending user {user_id}")
        
        # Get existing user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Set status to suspended
        user.status = UserStatus.SUSPENDED
        user.updated_at = datetime.now(UTC)
        
        # Save changes
        updated_user = await self.user_repository.update(user)
        logger.info(f"User {user_id} suspended successfully")
        
        return updated_user

class ActivateUserUseCase:
    """Use case for activating users"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> User:
        """Activate user by setting status to active"""
        logger.info(f"Activating user {user_id}")
        
        # Get existing user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Set status to active
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.now(UTC)
        
        # Save changes
        updated_user = await self.user_repository.update(user)
        logger.info(f"User {user_id} activated successfully")
        
        return updated_user

class ChangePasswordUseCase:
    """Use case for changing user password"""
    
    def __init__(self, 
                 user_repository: UserRepositoryPort,
                 auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self,
                     user_id: UUID,
                     current_password: str,
                     new_password: str) -> User:
        """Change user password"""
        logger.info(f"Changing password for user {user_id}")
        
        # Get existing user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Verify current password
        if not self.auth_service.verify_password(current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect")
        
        # Hash new password
        new_hashed_password = self.auth_service.hash_password(new_password)
        
        # Update password
        user.hashed_password = new_hashed_password
        user.updated_at = datetime.now(UTC)
        
        # Save changes
        updated_user = await self.user_repository.update(user)
        logger.info(f"Password changed successfully for user {user_id}")
        
        return updated_user

class GetUserStatsUseCase:
    """Use case for getting user statistics"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository
    
    async def execute(self) -> Dict[str, Any]:
        """Get user statistics"""
        logger.info("Getting user statistics")
        
        # Get total users
        total_users = await self.user_repository.count_users()
        
        # Get users by status
        active_users = await self.user_repository.count_users(status="active")
        inactive_users = await self.user_repository.count_users(status="inactive")
        suspended_users = await self.user_repository.count_users(status="suspended")
        
        # Get users by role
        users_by_role = {}
        for role in ["admin", "operator", "user", "viewer"]:
            count = await self.user_repository.count_users(role=role)
            users_by_role[role] = count
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "suspended_users": suspended_users,
            "users_by_role": users_by_role
        }