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
        """
                 Initializes the use case with a user repository and authentication service.
                 """
                 self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self,
                     email: str,
                     password: str,
                     full_name: str,
                     roles: List[str],
                     status: str = "active") -> User:
        """
                     Creates a new user with the specified email, password, full name, roles, and status.
                     
                     Validates that the email is unique, hashes the password, and converts role and status strings to their respective enums. Raises an error if the email already exists, or if any role or status is invalid. Persists the new user and returns the created user entity.
                     
                     Args:
                         email: The user's email address.
                         password: The user's plaintext password.
                         full_name: The user's full name.
                         roles: List of role names to assign to the user.
                         status: The user's initial status (default is "active").
                     
                     Returns:
                         The created User entity.
                     
                     Raises:
                         EntityAlreadyExistsError: If a user with the given email already exists.
                         ValidationError: If any provided role or status is invalid.
                     """
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
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> User:
        """
        Retrieves a user by their unique identifier.
        
        Raises:
            UserNotFoundError: If no user exists with the specified ID.
        
        Returns:
            The user entity corresponding to the given UUID.
        """
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return user

class GetUserByEmailUseCase:
    """Use case for retrieving user by email"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self, email: str) -> User:
        """
        Retrieves a user entity by email address.
        
        Raises:
            UserNotFoundError: If no user with the specified email exists.
        
        Returns:
            The user entity corresponding to the provided email.
        """
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"User with email {email} not found")
        
        return user

class ListUsersUseCase:
    """Use case for listing users with filters and pagination"""
    
    def __init__(self, user_repository: UserRepositoryPort):
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self,
                     status: Optional[str] = None,
                     role: Optional[str] = None,
                     search: Optional[str] = None,
                     page: int = 1,
                     size: int = 50) -> Dict[str, Any]:
        """
                     Retrieves a paginated list of users with optional filtering by status, role, and search term.
                     
                     Args:
                         status: Optional user status to filter by.
                         role: Optional user role to filter by.
                         search: Optional search term to filter users.
                         page: Page number for pagination (default is 1).
                         size: Number of users per page (default is 50).
                     
                     Returns:
                         A dictionary containing the list of users, total user count, current page, page size, and total number of pages.
                     """
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
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self,
                     user_id: UUID,
                     full_name: Optional[str] = None,
                     roles: Optional[List[str]] = None,
                     status: Optional[str] = None) -> User:
        """
                     Updates a user's full name, roles, or status by user ID.
                     
                     Raises:
                         UserNotFoundError: If the user with the given ID does not exist.
                         ValidationError: If any provided role or status is invalid.
                     
                     Args:
                         user_id: Unique identifier of the user to update.
                         full_name: New full name for the user, if provided.
                         roles: List of new roles for the user, if provided.
                         status: New status for the user, if provided.
                     
                     Returns:
                         The updated User entity.
                     """
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
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> bool:
        """
        Deletes a user by their unique identifier.
        
        Raises:
            UserNotFoundError: If no user exists with the specified ID.
        
        Returns:
            True if the user was successfully deleted, False otherwise.
        """
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
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> User:
        """
        Suspends a user by setting their status to SUSPENDED.
        
        Retrieves the user by ID, updates their status to suspended, updates the modification timestamp, and persists the changes. Raises UserNotFoundError if the user does not exist.
        
        Returns:
            The updated user entity with suspended status.
        """
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
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> User:
        """
        Activates a user by setting their status to active.
        
        Retrieves the user by ID, updates their status to active, refreshes the update timestamp, and persists the changes. Raises UserNotFoundError if the user does not exist.
        
        Returns:
            The updated user entity.
        """
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
        """
                 Initializes the use case with a user repository and authentication service.
                 """
                 self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self,
                     user_id: UUID,
                     current_password: str,
                     new_password: str) -> User:
        """
                     Changes a user's password after verifying the current password.
                     
                     Raises:
                         UserNotFoundError: If the user with the given ID does not exist.
                         ValidationError: If the current password is incorrect.
                     
                     Returns:
                         The updated user entity with the new password.
                     """
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
        """
        Initializes the use case with a user repository for data access.
        """
        self.user_repository = user_repository
    
    async def execute(self) -> Dict[str, Any]:
        """
        Retrieves aggregated statistics about users.
        
        Returns:
            A dictionary containing the total number of users, counts by status (active, inactive, suspended), and counts by role (admin, operator, user, viewer).
        """
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