from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Callable
from app.ports.door_repository_port import DoorRepositoryPort
from app.domain.entities.door import Door, DoorStatus, SecurityLevel
from app.infrastructure.database.models.door import DoorModel
from app.infrastructure.persistence.adapters.mappers.door_mapper import DoorMapper
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.domain.exceptions import RepositoryError

logger = logging.getLogger(__name__)

class SqlAlchemyDoorRepository(DoorRepositoryPort):
    """SQLAlchemy implementation of DoorRepositoryPort"""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
    
    async def create(self, door: Door) -> Door:
        async with self.session_factory() as db:
            try:
                door_model = DoorMapper.to_model(door)
                # Don't set ID for new doors, let DB generate it
                door_model.id = None
                
                db.add(door_model)
                await db.commit()
                await db.refresh(door_model)
                
                return DoorMapper.to_domain(door_model)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error creating door: {e}")
                raise RepositoryError(f"Error creating door: {e}") from e
    
    async def get_by_id(self, door_id: int) -> Optional[Door]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).where(DoorModel.id == door_id)
                )
                door_model = result.scalar_one_or_none()
                
                return DoorMapper.to_domain(door_model) if door_model else None
            except SQLAlchemyError as e:
                logger.error(f"Database error getting door by ID: {e}")
                raise RepositoryError(f"Error getting door: {e}") from e
    
    async def get_by_name(self, name: str) -> Optional[Door]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).where(DoorModel.name == name)
                )
                door_model = result.scalar_one_or_none()
                
                return DoorMapper.to_domain(door_model) if door_model else None
            except SQLAlchemyError as e:
                logger.error(f"Database error getting door by name: {e}")
                raise RepositoryError(f"Error getting door: {e}") from e
    
    async def get_by_location(self, location: str) -> List[Door]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).where(DoorModel.location == location)
                )
                door_models = result.scalars().all()
                
                return [DoorMapper.to_domain(model) for model in door_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error getting doors by location: {e}")
                raise RepositoryError(f"Error getting doors: {e}") from e
    
    async def update(self, door: Door) -> Door:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).where(DoorModel.id == door.id)
                )
                door_model = result.scalar_one_or_none()
                
                if not door_model:
                    raise RepositoryError(f"Door with ID {door.id} not found")
                
                door_model = DoorMapper.update_model_from_domain(door_model, door)
                await db.commit()
                await db.refresh(door_model)
                
                return DoorMapper.to_domain(door_model)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error updating door: {e}")
                raise RepositoryError(f"Error updating door: {e}") from e
    
    async def delete(self, door_id: int) -> bool:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).where(DoorModel.id == door_id)
                )
                door_model = result.scalar_one_or_none()
                
                if not door_model:
                    return False
                
                await db.delete(door_model)
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error deleting door: {e}")
                raise RepositoryError(f"Error deleting door: {e}") from e
    
    async def list_doors(self, skip: int = 0, limit: int = 100) -> List[Door]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).offset(skip).limit(limit)
                )
                door_models = result.scalars().all()
                
                return [DoorMapper.to_domain(model) for model in door_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error listing doors: {e}")
                raise RepositoryError(f"Error listing doors: {e}") from e
    
    async def get_active_doors(self) -> List[Door]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).where(DoorModel.status == DoorStatus.ACTIVE.value)
                )
                door_models = result.scalars().all()
                
                return [DoorMapper.to_domain(model) for model in door_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error getting active doors: {e}")
                raise RepositoryError(f"Error getting active doors: {e}") from e
    
    async def get_doors_by_security_level(self, security_level: str) -> List[Door]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(DoorModel).where(DoorModel.security_level == security_level)
                )
                door_models = result.scalars().all()
                
                return [DoorMapper.to_domain(model) for model in door_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error getting doors by security level: {e}")
                raise RepositoryError(f"Error getting doors by security level: {e}") from e