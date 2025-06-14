"""
Refactored Permission repository implementation using consistent session_factory pattern.
"""
from typing import Optional, List, Callable
from datetime import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from app.ports.permission_repository_port import PermissionRepositoryPort
from app.domain.entities.permission import Permission
from app.infrastructure.database.models.permission import PermissionModel
from app.infrastructure.persistence.adapters.mappers.permission_mapper import PermissionMapper
from app.domain.exceptions import RepositoryError
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class PermissionRepository(PermissionRepositoryPort):
    """SQLAlchemy implementation of Permission repository with consistent session management."""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initializes the PermissionRepository with a session factory and a permission mapper.
        
        Args:
            session_factory: A callable that returns a new AsyncSession instance for database operations.
        """
        self.session_factory = session_factory
        self.mapper = PermissionMapper()
    
    async def create(self, permission: Permission) -> Permission:
        """
        Creates a new permission record in the database.
        
        Converts the provided domain permission entity to a database model, persists it, and returns the newly created permission with its generated ID. Rolls back and raises a RepositoryError if a database error occurs.
        """
        async with self.session_factory() as session:
            try:
                model = self.mapper.to_model(permission)
                # Don't set ID for new permissions, let DB generate it
                model.id = None
                
                session.add(model)
                await session.commit()
                await session.refresh(model)
                
                logger.info(f"Created permission: {model.id}")
                return self.mapper.to_domain(model)
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error creating permission: {e}")
                raise RepositoryError(f"Failed to create permission: {e}") from e
    
    async def get_by_id(self, permission_id: UUID) -> Optional[Permission]:
        """
        Retrieves a permission by its unique identifier.
        
        Args:
            permission_id: The UUID of the permission to retrieve.
        
        Returns:
            The corresponding Permission entity if found, otherwise None.
        
        Raises:
            RepositoryError: If a database error occurs during retrieval.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).where(PermissionModel.id == permission_id)
                result = await session.execute(query)
                model = result.scalar_one_or_none()
                
                return self.mapper.to_domain(model) if model else None
                
            except SQLAlchemyError as e:
                logger.error(f"Database error getting permission by ID {permission_id}: {e}")
                raise RepositoryError(f"Failed to get permission: {e}") from e
    
    async def get_by_user_and_door_list(self, user_id: UUID, door_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions for a specific user and door combination.
        
        Args:
            user_id: The unique identifier of the user.
            door_id: The unique identifier of the door.
        
        Returns:
            A list of Permission entities associated with the given user and door.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).where(
                    and_(
                        PermissionModel.user_id == user_id,
                        PermissionModel.door_id == door_id
                    )
                )
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self.mapper.to_domain(model) for model in models]
                
            except SQLAlchemyError as e:
                logger.error(f"Database error getting permissions for user {user_id} and door {door_id}: {e}")
                raise RepositoryError(f"Failed to get permissions: {e}") from e
    
    async def get_by_user_and_door(self, user_id: UUID, door_id: UUID) -> Optional[Permission]:
        """
        Retrieves a single permission for a specific user and door.
        
        Returns the corresponding Permission entity if found, or None if no matching permission exists.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).where(
                    and_(
                        PermissionModel.user_id == user_id,
                        PermissionModel.door_id == door_id
                    )
                ).limit(1)
                result = await session.execute(query)
                model = result.scalar_one_or_none()
                
                return self.mapper.to_domain(model) if model else None
                
            except SQLAlchemyError as e:
                logger.error(f"Database error getting permission for user {user_id} and door {door_id}: {e}")
                raise RepositoryError(f"Failed to get permission: {e}") from e
    
    async def get_by_user_id(self, user_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific user.
        
        Args:
            user_id: The unique identifier of the user.
        
        Returns:
            A list of Permission entities belonging to the user.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).where(PermissionModel.user_id == user_id)
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self.mapper.to_domain(model) for model in models]
                
            except SQLAlchemyError as e:
                logger.error(f"Database error getting permissions for user {user_id}: {e}")
                raise RepositoryError(f"Failed to get permissions: {e}") from e
    
    async def get_by_door_id(self, door_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific door.
        
        Args:
            door_id: The unique identifier of the door.
        
        Returns:
            A list of Permission entities linked to the given door.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).where(PermissionModel.door_id == door_id)
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self.mapper.to_domain(model) for model in models]
                
            except SQLAlchemyError as e:
                logger.error(f"Database error getting permissions for door {door_id}: {e}")
                raise RepositoryError(f"Failed to get permissions: {e}") from e
    
    async def get_by_card_id(self, card_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific card ID.
        
        The card ID is assumed to be linked to a user, and all permissions for that user are returned.
        
        Args:
            card_id: The unique identifier of the card.
        
        Returns:
            A list of Permission entities associated with the card.
        """
        async with self.session_factory() as session:
            try:
                # Join with user model to get permissions by card
                query = select(PermissionModel).join(
                    PermissionModel.user
                ).where(
                    PermissionModel.user.has(id=card_id)  # Assuming card_id links to user
                )
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self.mapper.to_domain(model) for model in models]
                
            except SQLAlchemyError as e:
                logger.error(f"Database error getting permissions for card {card_id}: {e}")
                raise RepositoryError(f"Failed to get permissions: {e}") from e
    
    async def update(self, permission: Permission) -> Permission:
        """
        Updates an existing permission entity in the database.
        
        Raises:
            RepositoryError: If the permission does not exist or a database error occurs.
        
        Returns:
            The updated permission entity.
        """
        async with self.session_factory() as session:
            try:
                # Get existing model
                query = select(PermissionModel).where(PermissionModel.id == permission.id)
                result = await session.execute(query)
                existing_model = result.scalar_one_or_none()
                
                if not existing_model:
                    raise RepositoryError(f"Permission with ID {permission.id} not found")
                
                # Update model with new data
                updated_model = self.mapper.update_model_from_domain(existing_model, permission)
                await session.commit()
                await session.refresh(updated_model)
                
                logger.info(f"Updated permission: {updated_model.id}")
                return self.mapper.to_domain(updated_model)
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error updating permission: {e}")
                raise RepositoryError(f"Failed to update permission: {e}") from e
    
    async def delete(self, permission_id: UUID) -> bool:
        """
        Deletes a permission by its ID.
        
        Args:
            permission_id: The unique identifier of the permission to delete.
        
        Returns:
            True if the permission was deleted, False if not found.
        
        Raises:
            RepositoryError: If a database error occurs during deletion.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).where(PermissionModel.id == permission_id)
                result = await session.execute(query)
                model = result.scalar_one_or_none()
                
                if not model:
                    return False
                
                await session.delete(model)
                await session.commit()
                
                logger.info(f"Deleted permission: {permission_id}")
                return True
                
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error deleting permission: {e}")
                raise RepositoryError(f"Failed to delete permission: {e}") from e
    
    async def list_permissions(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        """
        Retrieves a paginated list of permissions.
        
        Args:
            skip: Number of records to skip before starting to collect the result set.
            limit: Maximum number of permissions to return.
        
        Returns:
            A list of Permission entities within the specified range.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).offset(skip).limit(limit)
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self.mapper.to_domain(model) for model in models]
                
            except SQLAlchemyError as e:
                logger.error(f"Database error listing permissions: {e}")
                raise RepositoryError(f"Failed to list permissions: {e}") from e
    
    async def get_active_permissions(self) -> List[Permission]:
        """
        Retrieves all permissions with an active status.
        
        Returns:
            A list of Permission entities that are currently marked as active.
        """
        async with self.session_factory() as session:
            try:
                query = select(PermissionModel).where(PermissionModel.status == "active")
                result = await session.execute(query)
                models = result.scalars().all()
                
                return [self.mapper.to_domain(model) for model in models]
                
            except SQLAlchemyError as e:
                logger.error(f"Database error getting active permissions: {e}")
                raise RepositoryError(f"Failed to get active permissions: {e}") from e
    
    async def check_access(self, user_id: UUID, door_id: UUID, current_time: time, current_day: str) -> bool:
        """
        Determines if a user has active permission to access a specific door at a given time and day.
        
        Checks for an active permission record matching the user and door, with validity constraints on time. Returns True if such a permission exists, otherwise False.
        
        Args:
            user_id: The unique identifier of the user.
            door_id: The unique identifier of the door.
            current_time: The current time to check against permission validity.
            current_day: The current day (not used in filtering but may be relevant for future logic).
        
        Returns:
            True if the user has access to the door at the specified time and day, otherwise False.
        
        Raises:
            RepositoryError: If a database error occurs during the access check.
        """
        async with self.session_factory() as session:
            try:
                # Complex query for access validation
                query = select(PermissionModel).where(
                    and_(
                        PermissionModel.user_id == user_id,
                        PermissionModel.door_id == door_id,
                        PermissionModel.status == "active",
                        or_(
                            PermissionModel.valid_from.is_(None),
                            PermissionModel.valid_from <= current_time
                        ),
                        or_(
                            PermissionModel.valid_until.is_(None),
                            PermissionModel.valid_until >= current_time
                        )
                    )
                )
                result = await session.execute(query)
                permission = result.scalar_one_or_none()
                
                return permission is not None
                
            except SQLAlchemyError as e:
                logger.error(f"Database error checking access for user {user_id} and door {door_id}: {e}")
                raise RepositoryError(f"Failed to check access: {e}") from e