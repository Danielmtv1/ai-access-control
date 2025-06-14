"""
Base seeder class providing common functionality for database seeding.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


class BaseSeeder(ABC):
    """Abstract base class for database seeders."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._created_objects: List[Any] = []
    
    @abstractmethod
    async def seed(self) -> Dict[str, Any]:
        """Seed the database and return created objects."""
        pass
    
    async def cleanup(self):
        """Clean up created objects (in reverse order)."""
        for obj in reversed(self._created_objects):
            try:
                await self.session.delete(obj)
            except Exception as e:
                logger.warning(f"Failed to delete {obj}: {e}")
        
        try:
            await self.session.commit()
        except Exception as e:
            logger.error(f"Failed to commit cleanup: {e}")
            await self.session.rollback()
        
        self._created_objects.clear()
    
    async def _save_object(self, obj: Any) -> Any:
        """Save an object to the database and track it for cleanup."""
        self.session.add(obj)
        await self.session.flush()  # Get the ID without committing
        await self.session.refresh(obj)  # Refresh to get all attributes
        self._created_objects.append(obj)
        return obj
    
    async def _save_objects(self, objects: List[Any]) -> List[Any]:
        """Save multiple objects to the database."""
        saved_objects = []
        for obj in objects:
            saved_obj = await self._save_object(obj)
            saved_objects.append(saved_obj)
        return saved_objects
    
    async def _commit_changes(self):
        """Commit all changes to the database."""
        try:
            await self.session.commit()
            logger.info(f"Successfully committed {len(self._created_objects)} objects")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            await self.session.rollback()
            raise
    
    def get_created_objects(self) -> List[Any]:
        """Get list of all created objects."""
        return self._created_objects.copy()
    
    def get_created_count(self) -> int:
        """Get count of created objects."""
        return len(self._created_objects)


class TransactionalSeeder(BaseSeeder):
    """Seeder that automatically handles transactions."""
    
    async def seed_with_transaction(self) -> Dict[str, Any]:
        """Seed database within a transaction that can be rolled back."""
        try:
            result = await self.seed()
            await self._commit_changes()
            return result
        except Exception as e:
            logger.error(f"Seeding failed, rolling back: {e}")
            await self.session.rollback()
            raise
    
    async def seed_and_rollback(self) -> Dict[str, Any]:
        """Seed database and then rollback (useful for testing seeder logic)."""
        try:
            result = await self.seed()
            logger.info("Seeding completed, rolling back for testing")
            await self.session.rollback()
            self._created_objects.clear()  # Objects are no longer valid
            return result
        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            await self.session.rollback()
            raise


class BulkSeeder(BaseSeeder):
    """Seeder optimized for bulk operations."""
    
    async def bulk_save_objects(self, objects: List[Any]) -> List[Any]:
        """Bulk save objects for better performance."""
        try:
            self.session.add_all(objects)
            await self.session.flush()
            
            # Refresh all objects to get IDs and computed fields
            for obj in objects:
                await self.session.refresh(obj)
                self._created_objects.append(obj)
            
            return objects
        except Exception as e:
            logger.error(f"Bulk save failed: {e}")
            await self.session.rollback()
            raise
    
    async def execute_raw_sql(self, sql: str, params: Optional[Dict[str, Any]] = None):
        """Execute raw SQL for complex seeding operations."""
        try:
            await self.session.execute(sql, params or {})
            logger.debug(f"Executed SQL: {sql}")
        except Exception as e:
            logger.error(f"Raw SQL execution failed: {e}")
            raise