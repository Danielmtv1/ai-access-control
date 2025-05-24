from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Callable
from ...ports.user_repository_port import UserRepositoryPort
from ...domain.entities.user import User
from ..persistence.user_model import UserModel
from ..persistence.mappers.user_mapper import UserMapper
from sqlalchemy.exc import SQLAlchemyError
import logging
from ...domain.exceptions import RepositoryError

logger = logging.getLogger(__name__)

class SqlAlchemyUserRepository(UserRepositoryPort):
    """SQLAlchemy implementation of UserRepositoryPort"""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
    
    async def create(self, user: User) -> User:
        async with self.session_factory() as db:
            try:
                user_model = UserMapper.to_model(user)
                # Don't set ID for new users, let DB generate it
                user_model.id = None
                
                db.add(user_model)
                await db.commit()
                await db.refresh(user_model)
                
                return UserMapper.to_domain(user_model)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error creating user: {e}")
                raise RepositoryError(f"Error creating user: {e}") from e
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(UserModel).where(UserModel.id == user_id)
                )
                user_model = result.scalar_one_or_none()
                
                return UserMapper.to_domain(user_model) if user_model else None
            except SQLAlchemyError as e:
                logger.error(f"Database error getting user by ID: {e}")
                raise RepositoryError(f"Error getting user: {e}") from e
    
    async def get_by_email(self, email: str) -> Optional[User]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(UserModel).where(UserModel.email == email)
                )
                user_model = result.scalar_one_or_none()
                
                return UserMapper.to_domain(user_model) if user_model else None
            except SQLAlchemyError as e:
                logger.error(f"Database error getting user by email: {e}")
                raise RepositoryError(f"Error getting user: {e}") from e
    
    async def update(self, user: User) -> User:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(UserModel).where(UserModel.id == user.id)
                )
                user_model = result.scalar_one_or_none()
                
                if not user_model:
                    raise RepositoryError(f"User with ID {user.id} not found")
                
                user_model = UserMapper.update_model_from_domain(user_model, user)
                await db.commit()
                await db.refresh(user_model)
                
                return UserMapper.to_domain(user_model)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error updating user: {e}")
                raise RepositoryError(f"Error updating user: {e}") from e
    
    async def delete(self, user_id: int) -> bool:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(UserModel).where(UserModel.id == user_id)
                )
                user_model = result.scalar_one_or_none()
                
                if not user_model:
                    return False
                
                await db.delete(user_model)
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error deleting user: {e}")
                raise RepositoryError(f"Error deleting user: {e}") from e
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(UserModel).offset(skip).limit(limit)
                )
                user_models = result.scalars().all()
                
                return [UserMapper.to_domain(model) for model in user_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error listing users: {e}")
                raise RepositoryError(f"Error listing users: {e}") from e 