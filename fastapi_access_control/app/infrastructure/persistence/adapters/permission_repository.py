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
        self.session_factory = session_factory
        self.mapper = PermissionMapper()
    
    async def create(self, permission: Permission) -> Permission:
        """Create a new permission."""
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
        """Get permission by ID."""
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
        """Get permissions for user and door."""
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
        """Get single permission for user and door."""
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
        """Get all permissions for a user."""
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
        """Get all permissions for a door."""
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
        """Get all permissions for a card."""
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
        """Update an existing permission."""
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
        """Delete a permission."""
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
        """List permissions with pagination."""
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
        """Get all active permissions."""
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
        """Check if user has access to door at current time and day."""
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