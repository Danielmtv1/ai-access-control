"""
Integration tests for repository implementations with real database.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, time
from uuid import uuid4

from app.shared.database.session import get_db
from app.infrastructure.persistence.adapters.card_repository import SqlAlchemyCardRepository
from app.infrastructure.persistence.adapters.door_repository import SqlAlchemyDoorRepository
from app.infrastructure.persistence.adapters.user_repository import SqlAlchemyUserRepository
from app.infrastructure.persistence.adapters.permission_repository import PermissionRepository
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.door import Door, DoorStatus, SecurityLevel, DoorType
from app.domain.entities.user import User, Role, UserStatus
from app.domain.entities.permission import Permission, PermissionStatus
from app.domain.exceptions import RepositoryError


class TestRepositoryIntegrations:
    """Integration tests for repository implementations."""
    
    @pytest.fixture
    async def db_session(self):
        """Database session for testing."""
        async for session in get_db():
            yield session
            break
    
    @pytest.fixture
    def card_repository(self, db_session):
        """Card repository instance."""
        return SqlAlchemyCardRepository(lambda: db_session)
    
    @pytest.fixture
    def door_repository(self, db_session):
        """Door repository instance."""
        return SqlAlchemyDoorRepository(lambda: db_session)
    
    @pytest.fixture
    def user_repository(self, db_session):
        """User repository instance."""
        return SqlAlchemyUserRepository(lambda: db_session)
    
    @pytest.fixture
    def permission_repository(self, db_session):
        """Permission repository instance."""
        return PermissionRepository(db_session)
    
    @pytest.fixture
    def sample_user_entity(self):
        """Sample user domain entity."""
        return User(
            id=uuid4(),
            email="integration@test.com",
            hashed_password="hashed_password",
            full_name="Integration Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    async def test_user_repository_crud_operations(self, user_repository, sample_user_entity):
        """Test complete CRUD operations for user repository."""
        # Create
        created_user = await user_repository.create(sample_user_entity)
        assert created_user.id is not None
        assert created_user.email == sample_user_entity.email
        
        # Read
        retrieved_user = await user_repository.get_by_id(created_user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == sample_user_entity.email
        
        # Update
        retrieved_user.full_name = "Updated Name"
        updated_user = await user_repository.update(retrieved_user)
        assert updated_user.full_name == "Updated Name"
        
        # List
        users = await user_repository.list_users(limit=10)
        assert len(users) >= 1
        
        # Get by email
        user_by_email = await user_repository.get_by_email(sample_user_entity.email)
        assert user_by_email is not None
        assert user_by_email.id == created_user.id
        
        # Delete
        deleted = await user_repository.delete(created_user.id)
        assert deleted is True
        
        # Verify deletion
        deleted_user = await user_repository.get_by_id(created_user.id)
        assert deleted_user is None
    
    @pytest.mark.asyncio
    async def test_door_repository_crud_operations(self, door_repository):
        """Test complete CRUD operations for door repository."""
        # Create door entity
        door_entity = Door(
            id=None,  # Will be assigned by database
            name="Integration Test Door",
            location="Test Building",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            description="Test door for integration tests"
        )
        
        # Create
        created_door = await door_repository.create(door_entity)
        assert created_door.id is not None
        assert created_door.name == "Integration Test Door"
        
        # Read
        retrieved_door = await door_repository.get_by_id(created_door.id)
        assert retrieved_door is not None
        assert retrieved_door.name == "Integration Test Door"
        
        # Update
        retrieved_door.description = "Updated description"
        updated_door = await door_repository.update(retrieved_door)
        assert updated_door.description == "Updated description"
        
        # List active doors
        active_doors = await door_repository.get_active_doors()
        assert len(active_doors) >= 1
        
        # Get by name
        door_by_name = await door_repository.get_by_name("Integration Test Door")
        assert door_by_name is not None
        assert door_by_name.id == created_door.id
        
        # Delete
        deleted = await door_repository.delete(created_door.id)
        assert deleted is True
        
        # Verify deletion
        deleted_door = await door_repository.get_by_id(created_door.id)
        assert deleted_door is None
    
    @pytest.mark.asyncio
    async def test_card_repository_crud_operations(self, card_repository, user_repository, sample_user_entity):
        """Test complete CRUD operations for card repository."""
        # First create a user
        created_user = await user_repository.create(sample_user_entity)
        
        # Create card entity
        card_entity = Card(
            id=uuid4(),
            user_id=created_user.id,
            card_id="INTEGRATION001",
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=datetime.now(timezone.utc),
            valid_until=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            use_count=0
        )
        
        # Create
        created_card = await card_repository.create(card_entity)
        assert created_card.id is not None
        assert created_card.card_id == "INTEGRATION001"
        
        # Read by ID
        retrieved_card = await card_repository.get_by_id(created_card.id)
        assert retrieved_card is not None
        assert retrieved_card.card_id == "INTEGRATION001"
        
        # Read by card_id
        card_by_card_id = await card_repository.get_by_card_id("INTEGRATION001")
        assert card_by_card_id is not None
        assert card_by_card_id.id == created_card.id
        
        # Update
        retrieved_card.card_type = CardType.CONTRACTOR
        updated_card = await card_repository.update(retrieved_card)
        assert updated_card.card_type == CardType.CONTRACTOR
        
        # List by user
        user_cards = await card_repository.get_by_user_id(created_user.id)
        assert len(user_cards) >= 1
        
        # Get active cards
        active_cards = await card_repository.get_active_cards()
        assert len(active_cards) >= 1
        
        # Delete
        deleted = await card_repository.delete(created_card.id)
        assert deleted is True
        
        # Cleanup user
        await user_repository.delete(created_user.id)
    
    @pytest.mark.asyncio
    async def test_permission_repository_crud_operations(self, permission_repository, user_repository, 
                                                         door_repository, sample_user_entity):
        """Test complete CRUD operations for permission repository."""
        # Create user and door first
        created_user = await user_repository.create(sample_user_entity)
        
        door_entity = Door(
            id=None,
            name="Permission Test Door",
            location="Test Location",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.LOW,
            status=DoorStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        created_door = await door_repository.create(door_entity)
        
        # Create permission entity
        permission_entity = Permission(
            id=None,
            user_id=int(str(created_user.id)[:8], 16),  # Convert UUID to int for permission
            door_id=created_door.id,
            status=PermissionStatus.ACTIVE,
            valid_from=datetime.now(timezone.utc),
            created_by=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            access_schedule='{"days": ["mon", "tue", "wed"], "start": "09:00", "end": "17:00"}'
        )
        
        # Create
        created_permission = await permission_repository.create(permission_entity)
        assert created_permission.id is not None
        assert created_permission.user_id == permission_entity.user_id
        
        # Read
        retrieved_permission = await permission_repository.get_by_id(created_permission.id)
        assert retrieved_permission is not None
        assert retrieved_permission.door_id == created_door.id
        
        # Update
        retrieved_permission.access_schedule = '{"days": ["mon", "tue"], "start": "08:00", "end": "18:00"}'
        updated_permission = await permission_repository.update(retrieved_permission)
        assert "08:00" in updated_permission.access_schedule
        
        # List permissions
        all_permissions = await permission_repository.list_permissions(limit=10)
        assert len(all_permissions) >= 1
        
        # Get by user and door
        user_door_permission = await permission_repository.get_by_user_and_door(
            permission_entity.user_id, 
            created_door.id
        )
        assert user_door_permission is not None
        
        # Check access
        has_access = await permission_repository.check_access(
            permission_entity.user_id,
            created_door.id,
            time(10, 0),
            "mon"
        )
        assert has_access is True
        
        # Delete
        deleted = await permission_repository.delete(created_permission.id)
        assert deleted is True
        
        # Cleanup
        await door_repository.delete(created_door.id)
        await user_repository.delete(created_user.id)
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(self, user_repository):
        """Test repository error handling with invalid data."""
        # Try to get non-existent user
        non_existent_user = await user_repository.get_by_id(uuid4())
        assert non_existent_user is None
        
        # Try to update non-existent user
        fake_user = User(
            id=uuid4(),
            email="nonexistent@test.com",
            hashed_password="hash",
            full_name="Fake User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        with pytest.raises(RepositoryError):
            await user_repository.update(fake_user)
        
        # Try to delete non-existent user
        deleted = await user_repository.delete(uuid4())
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_concurrent_repository_operations(self, user_repository):
        """Test concurrent repository operations."""
        import asyncio
        
        # Create multiple users concurrently
        async def create_user(index):
            user = User(
                id=uuid4(),
                email=f"concurrent{index}@test.com",
                hashed_password="hash",
                full_name=f"Concurrent User {index}",
                roles=[Role.USER],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            return await user_repository.create(user)
        
        # Create 5 users concurrently
        tasks = [create_user(i) for i in range(5)]
        users = await asyncio.gather(*tasks)
        
        # All should be created successfully
        assert len(users) == 5
        for user in users:
            assert user.id is not None
        
        # Cleanup
        for user in users:
            await user_repository.delete(user.id)
    
    @pytest.mark.asyncio
    async def test_repository_transaction_rollback(self, db_session, user_repository):
        """Test repository transaction rollback on errors."""
        # Create a user
        user = User(
            id=uuid4(),
            email="rollback@test.com",
            hashed_password="hash",
            full_name="Rollback Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        created_user = await user_repository.create(user)
        assert created_user.id is not None
        
        # Try to create another user with same email (should fail)
        duplicate_user = User(
            id=uuid4(),
            email="rollback@test.com",  # Same email
            hashed_password="hash",
            full_name="Duplicate User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        with pytest.raises(RepositoryError):
            await user_repository.create(duplicate_user)
        
        # Original user should still exist
        existing_user = await user_repository.get_by_email("rollback@test.com")
        assert existing_user is not None
        assert existing_user.full_name == "Rollback Test User"
        
        # Cleanup
        await user_repository.delete(created_user.id)
    
    @pytest.mark.asyncio
    async def test_repository_pagination(self, user_repository):
        """Test repository pagination functionality."""
        # Create multiple users for pagination test
        users_to_create = []
        for i in range(15):
            user = User(
                id=uuid4(),
                email=f"pagination{i}@test.com",
                hashed_password="hash",
                full_name=f"Pagination User {i}",
                roles=[Role.USER],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            users_to_create.append(user)
        
        # Create all users
        created_users = []
        for user in users_to_create:
            created = await user_repository.create(user)
            created_users.append(created)
        
        try:
            # Test pagination
            page1 = await user_repository.list_users(skip=0, limit=5)
            page2 = await user_repository.list_users(skip=5, limit=5)
            page3 = await user_repository.list_users(skip=10, limit=5)
            
            # Each page should have expected number of results
            assert len(page1) == 5
            assert len(page2) == 5
            assert len(page3) >= 5  # At least our created users
            
            # Pages should not overlap
            page1_ids = {user.id for user in page1}
            page2_ids = {user.id for user in page2}
            assert page1_ids.isdisjoint(page2_ids)
            
        finally:
            # Cleanup
            for user in created_users:
                await user_repository.delete(user.id)