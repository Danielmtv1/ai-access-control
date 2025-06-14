import pytest
import json
from datetime import datetime, timezone, UTC, timedelta, time
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.persistence.adapters.door_repository import SqlAlchemyDoorRepository
from app.infrastructure.database.models.door import DoorModel
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule
from app.domain.exceptions import RepositoryError

class TestSqlAlchemyDoorRepository:
    """Test cases for SqlAlchemyDoorRepository"""
    
    @pytest.fixture
    async def sample_door_model(self, db_session: AsyncSession):
        """Create a sample door for testing"""
        schedule_data = json.dumps({
            'days_of_week': [0, 1, 2, 3, 4],
            'start_time': '09:00',
            'end_time': '18:00'
        })
        
        door_model = DoorModel(
            name="Main Entrance",
            location="Building A",
            description="Main building entrance",
            door_type="entrance",
            security_level="medium",
            status="active",
            requires_pin=False,
            max_attempts=3,
            lockout_duration=300,
            failed_attempts=0,
            default_schedule=schedule_data
        )
        db_session.add(door_model)
        await db_session.commit()
        await db_session.refresh(door_model)
        return door_model
    
    @pytest.fixture
    def door_repository(self, db_session: AsyncSession):
        """Create door repository for testing"""
        def session_factory():
            return db_session
        return SqlAlchemyDoorRepository(session_factory)
    
    async def test_create_door(self, door_repository: SqlAlchemyDoorRepository):
        """Test door creation"""
        now = datetime.now(UTC).replace(tzinfo=None)
        schedule = AccessSchedule(
            days_of_week=[0, 1, 2, 3, 4],
            start_time=time(9, 0),
            end_time=time(18, 0)
        )
        
        door = Door(
            id=0,  # Will be set by database
            name="Side Entrance",
            location="Building B",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.LOW,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            description="Side building entrance",
            default_schedule=schedule,
            requires_pin=True,
            max_attempts=5,
            lockout_duration=600,
            failed_attempts=0
        )
        
        result = await door_repository.create(door)
        
        assert result.id > 0
        assert result.name == "Side Entrance"
        assert result.location == "Building B"
        assert result.door_type == DoorType.ENTRANCE
        assert result.security_level == SecurityLevel.LOW
        assert result.requires_pin is True
        assert result.default_schedule is not None
        assert result.default_schedule.days_of_week == [0, 1, 2, 3, 4]
    
    async def test_create_door_without_schedule(self, door_repository: SqlAlchemyDoorRepository):
        """Test door creation without schedule"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        door = Door(
            id=0,
            name="Emergency Exit",
            location="Building C",
            door_type=DoorType.EMERGENCY,
            security_level=SecurityLevel.CRITICAL,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            default_schedule=None
        )
        
        result = await door_repository.create(door)
        
        assert result.id > 0
        assert result.name == "Emergency Exit"
        assert result.default_schedule is None
    
    async def test_get_by_id(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test getting door by ID"""
        result = await door_repository.get_by_id(sample_door_model.id)
        
        assert result is not None
        assert result.id == sample_door_model.id
        assert result.name == "Main Entrance"
        assert result.door_type == DoorType.ENTRANCE
        assert result.default_schedule is not None
        assert result.default_schedule.days_of_week == [0, 1, 2, 3, 4]
    
    async def test_get_by_id_not_found(self, door_repository: SqlAlchemyDoorRepository):
        """Test getting door by ID when door doesn't exist"""
        result = await door_repository.get_by_id(999)
        
        assert result is None
    
    async def test_get_by_name(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test getting door by name"""
        result = await door_repository.get_by_name("Main Entrance")
        
        assert result is not None
        assert result.id == sample_door_model.id
        assert result.name == "Main Entrance"
    
    async def test_get_by_name_not_found(self, door_repository: SqlAlchemyDoorRepository):
        """Test getting door by name when door doesn't exist"""
        result = await door_repository.get_by_name("Nonexistent Door")
        
        assert result is None
    
    async def test_get_by_location(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test getting doors by location"""
        result = await door_repository.get_by_location("Building A")
        
        assert len(result) >= 1
        assert any(door.id == sample_door_model.id for door in result)
        assert all(door.location == "Building A" for door in result)
    
    async def test_get_by_location_no_doors(self, door_repository: SqlAlchemyDoorRepository):
        """Test getting doors by location when no doors exist"""
        result = await door_repository.get_by_location("Nonexistent Building")
        
        assert len(result) == 0
    
    async def test_update_door(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test updating door"""
        # Get the door first
        door = await door_repository.get_by_id(sample_door_model.id)
        assert door is not None
        
        # Update the door
        door.name = "Main Entrance Updated"
        door.security_level = SecurityLevel.HIGH
        door.requires_pin = True
        
        result = await door_repository.update(door)
        
        assert result.name == "Main Entrance Updated"
        assert result.security_level == SecurityLevel.HIGH
        assert result.requires_pin is True
        assert result.updated_at > door.created_at
    
    async def test_update_door_schedule(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test updating door with new schedule"""
        # Get the door first
        door = await door_repository.get_by_id(sample_door_model.id)
        assert door is not None
        
        # Update with new schedule
        new_schedule = AccessSchedule(
            days_of_week=[5, 6],  # Weekends only
            start_time=time(10, 0),
            end_time=time(16, 0)
        )
        door.default_schedule = new_schedule
        
        result = await door_repository.update(door)
        
        assert result.default_schedule is not None
        assert result.default_schedule.days_of_week == [5, 6]
        assert result.default_schedule.start_time == time(10, 0)
        assert result.default_schedule.end_time == time(16, 0)
    
    async def test_update_door_remove_schedule(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test updating door to remove schedule"""
        # Get the door first
        door = await door_repository.get_by_id(sample_door_model.id)
        assert door is not None
        assert door.default_schedule is not None  # Initially has schedule
        
        # Remove schedule
        door.default_schedule = None
        
        result = await door_repository.update(door)
        
        assert result.default_schedule is None
    
    async def test_update_door_not_found(self, door_repository: SqlAlchemyDoorRepository):
        """Test updating door that doesn't exist"""
        now = datetime.now(UTC).replace(tzinfo=None)
        door = Door(
            id=999,  # Non-existent ID
            name="Nonexistent Door",
            location="Building Z",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        with pytest.raises(RepositoryError, match="Door with ID 999 not found"):
            await door_repository.update(door)
    
    async def test_delete_door(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test deleting door"""
        result = await door_repository.delete(sample_door_model.id)
        
        assert result is True
        
        # Verify door is deleted
        deleted_door = await door_repository.get_by_id(sample_door_model.id)
        assert deleted_door is None
    
    async def test_delete_door_not_found(self, door_repository: SqlAlchemyDoorRepository):
        """Test deleting door that doesn't exist"""
        result = await door_repository.delete(999)
        
        assert result is False
    
    async def test_list_doors(self, door_repository: SqlAlchemyDoorRepository, sample_door_model: DoorModel):
        """Test listing doors with pagination"""
        result = await door_repository.list_doors(skip=0, limit=10)
        
        assert len(result) >= 1
        assert any(door.id == sample_door_model.id for door in result)
    
    async def test_list_doors_pagination(self, door_repository: SqlAlchemyDoorRepository, db_session: AsyncSession):
        """Test doors pagination"""
        # Create multiple doors for pagination testing
        for i in range(5):
            door_model = DoorModel(
                name=f"Test Door {i+10}",
                location=f"Building {chr(65+i)}",
                door_type="entrance",
                security_level="low",
                status="active",
                requires_pin=False,
                max_attempts=3,
                lockout_duration=300,
                failed_attempts=0
            )
            db_session.add(door_model)
        await db_session.commit()
        
        # Test pagination
        first_page = await door_repository.list_doors(skip=0, limit=3)
        second_page = await door_repository.list_doors(skip=3, limit=3)
        
        assert len(first_page) == 3
        assert len(second_page) >= 1
        
        # Ensure no overlap
        first_page_ids = {door.id for door in first_page}
        second_page_ids = {door.id for door in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)
    
    async def test_get_active_doors(self, door_repository: SqlAlchemyDoorRepository, db_session: AsyncSession):
        """Test getting only active doors"""
        # Create inactive door
        inactive_door = DoorModel(
            name="Inactive Door",
            location="Building Z",
            door_type="entrance",
            security_level="low",
            status="inactive",
            requires_pin=False,
            max_attempts=3,
            lockout_duration=300,
            failed_attempts=0
        )
        db_session.add(inactive_door)
        await db_session.commit()
        
        result = await door_repository.get_active_doors()
        
        # Should only return active doors
        assert all(door.status == DoorStatus.ACTIVE for door in result)
        assert not any(door.name == "Inactive Door" for door in result)
    
    async def test_get_doors_by_security_level(self, door_repository: SqlAlchemyDoorRepository, db_session: AsyncSession):
        """Test getting doors by security level"""
        # Create high security door
        high_security_door = DoorModel(
            name="High Security Door",
            location="Building X",
            door_type="entrance",
            security_level="high",
            status="active",
            requires_pin=True,
            max_attempts=1,
            lockout_duration=900,
            failed_attempts=0
        )
        db_session.add(high_security_door)
        await db_session.commit()
        
        result = await door_repository.get_doors_by_security_level("high")
        
        # Should only return high security doors
        assert all(door.security_level == SecurityLevel.HIGH for door in result)
        assert any(door.name == "High Security Door" for door in result)
    
    async def test_get_doors_by_security_level_no_doors(self, door_repository: SqlAlchemyDoorRepository):
        """Test getting doors by security level when no doors exist"""
        result = await door_repository.get_doors_by_security_level("critical")
        
        # Should return empty list for security level with no doors
        assert len(result) == 0