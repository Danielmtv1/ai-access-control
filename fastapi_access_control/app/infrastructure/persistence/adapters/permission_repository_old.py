"""
Permission repository implementation.
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
    """SQLAlchemy implementation of Permission repository."""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """
        Initializes the PermissionRepository with a session factory and a permission mapper.
        
        Args:
            session_factory: A callable that returns a new asynchronous SQLAlchemy session.
        """
        self.session_factory = session_factory
        self.mapper = PermissionMapper()
    
    async def create(self, permission: Permission) -> Permission:
        """
        Creates a new permission record in the database.
        
        Args:
            permission: The permission domain entity to be created.
        
        Returns:
            The created permission entity with database-generated fields populated.
        
        Raises:
            RepositoryError: If a database error occurs during creation.
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
            The corresponding Permission domain object if found, otherwise None.
        
        Raises:
            RepositoryError: If a database error occurs during retrieval.
        """
        try:
            query = select(PermissionModel).where(PermissionModel.id == permission_id)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            return self.mapper.to_domain(model) if model else None
            
        except Exception as e:
            logger.error(f"Error getting permission by ID {permission_id}: {str(e)}")
            raise RepositoryError(f"Failed to get permission: {str(e)}")
    
    async def get_by_user_and_door_list(self, user_id: UUID, door_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific user and door.
        
        Args:
            user_id: The unique identifier of the user.
            door_id: The unique identifier of the door.
        
        Returns:
            A list of Permission domain objects matching the given user and door.
        """
        try:
            query = select(PermissionModel).where(
                and_(
                    PermissionModel.user_id == user_id,
                    PermissionModel.door_id == door_id
                )
            )
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self.mapper.to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id} and door {door_id}: {str(e)}")
            raise RepositoryError(f"Failed to get permissions: {str(e)}")
    
    async def get_by_user_and_door(self, user_id: UUID, door_id: UUID) -> Optional[Permission]:
        """
        Retrieves the permission for a specific user and door combination.
        
        Args:
            user_id: The unique identifier of the user.
            door_id: The unique identifier of the door.
        
        Returns:
            The corresponding Permission object if found, otherwise None.
        
        Raises:
            RepositoryError: If a database error occurs during retrieval.
        """
        try:
            query = select(PermissionModel).where(
                and_(
                    PermissionModel.user_id == user_id,
                    PermissionModel.door_id == door_id
                )
            ).limit(1)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            logger.info(f"Permission query result: model={model}")
            if model:
                logger.info(f"Model data: id={model.id}, status={model.status}, user_id={model.user_id}")
                domain_obj = self.mapper.to_domain(model)
                logger.info(f"Mapped domain object: {domain_obj}")
                return domain_obj
            else:
                logger.info("No permission model found")
                return None
            return self.mapper.to_domain(model) if model else None
            
        except Exception as e:
            logger.error(f"Error getting permission for user {user_id} and door {door_id}: {str(e)}")
            raise RepositoryError(f"Failed to get permission: {str(e)}")
    
    async def get_by_user_id(self, user_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific user.
        
        Args:
            user_id: The unique identifier of the user.
        
        Returns:
            A list of Permission domain objects for the given user.
        """
        try:
            query = select(PermissionModel).where(PermissionModel.user_id == user_id)
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self.mapper.to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error getting permissions for user {user_id}: {str(e)}")
            raise RepositoryError(f"Failed to get permissions: {str(e)}")
    
    async def get_by_door_id(self, door_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific door.
        
        Args:
            door_id: The unique identifier of the door.
        
        Returns:
            A list of Permission domain objects linked to the specified door.
        """
        try:
            query = select(PermissionModel).where(PermissionModel.door_id == door_id)
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self.mapper.to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error getting permissions for door {door_id}: {str(e)}")
            raise RepositoryError(f"Failed to get permissions: {str(e)}")
    
    async def get_by_card_id(self, card_id: UUID) -> List[Permission]:
        """
        Retrieves all permissions associated with a specific card ID.
        
        Args:
        	card_id: The unique identifier of the card.
        
        Returns:
        	A list of Permission domain objects linked to the given card.
        """
        try:
            # This requires joining with cards table to get user_id
            # For now, we'll need to implement this based on the card-user relationship
            # Since cards belong to users, we can get permissions via user_id
            query = select(PermissionModel).where(PermissionModel.card_number == str(card_id))
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self.mapper.to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error getting permissions for card {card_id}: {str(e)}")
            raise RepositoryError(f"Failed to get permissions: {str(e)}")
    
    async def update(self, permission: Permission) -> Permission:
        """
        Updates an existing permission record in the database.
        
        Args:
        	permission: The domain Permission entity containing updated data.
        
        Returns:
        	The updated Permission entity.
        
        Raises:
        	RepositoryError: If the permission does not exist or the update fails.
        """
        try:
            query = select(PermissionModel).where(PermissionModel.id == permission.id)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            if not model:
                raise RepositoryError(f"Permission {permission.id} not found")
            
            # Update model using mapper
            updated_model = self.mapper.update_model_from_domain(model, permission)
            
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info(f"Updated permission: {model.id}")
            return self.mapper.to_domain(model)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating permission {permission.id}: {str(e)}")
            raise RepositoryError(f"Failed to update permission: {str(e)}")
    
    async def delete(self, permission_id: UUID) -> bool:
        """
        Deletes a permission by its unique identifier.
        
        Args:
            permission_id: The UUID of the permission to delete.
        
        Returns:
            True if the permission was found and deleted, False if not found.
        
        Raises:
            RepositoryError: If an error occurs during the deletion process.
        """
        try:
            query = select(PermissionModel).where(PermissionModel.id == permission_id)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            await self.session.delete(model)
            await self.session.commit()
            
            logger.info(f"Deleted permission: {permission_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting permission {permission_id}: {str(e)}")
            raise RepositoryError(f"Failed to delete permission: {str(e)}")
    
    async def list_permissions(self, skip: int = 0, limit: int = 100) -> List[Permission]:
        """
        Retrieves a paginated list of permissions.
        
        Args:
            skip: Number of records to skip before starting to collect the result set.
            limit: Maximum number of permissions to return.
        
        Returns:
            A list of Permission domain entities within the specified range.
        """
        try:
            query = select(PermissionModel).offset(skip).limit(limit)
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self.mapper.to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error listing permissions: {str(e)}")
            raise RepositoryError(f"Failed to list permissions: {str(e)}")
    
    async def get_active_permissions(self) -> List[Permission]:
        """
        Retrieves all permissions that are currently active.
        
        Returns:
            A list of Permission domain objects representing active permissions.
        """
        try:
            query = select(PermissionModel).where(PermissionModel.is_active == True)
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self.mapper.to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error getting active permissions: {str(e)}")
            raise RepositoryError(f"Failed to get active permissions: {str(e)}")
    
    async def check_access(self, user_id: UUID, door_id: UUID, current_time: time, current_day: str) -> bool:
        """
        Determines whether a user has access to a specific door at a given time and day.
        
        Args:
            user_id: The unique identifier of the user.
            door_id: The unique identifier of the door.
            current_time: The current time to check access against.
            current_day: The current day of the week as a string.
        
        Returns:
            True if the user has access to the door at the specified time and day, otherwise False.
        
        Raises:
            RepositoryError: If an error occurs during the access check process.
        """
        try:
            # Get permission for user and door combination
            permission = await self.get_by_user_and_door(user_id, door_id)
            
            if not permission:
                return False
            
            # Use the domain entity's business logic to check access
            from datetime import datetime, timezone
            current_datetime = datetime.combine(datetime.now().date(), current_time)
            
            return permission.can_access_door(door_id)
            
        except Exception as e:
            logger.error(f"Error checking access for user {user_id} and door {door_id}: {str(e)}")
            raise RepositoryError(f"Failed to check access: {str(e)}")