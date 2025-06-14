import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone, UTC, timedelta, time
from app.application.use_cases.door_use_cases import (
    CreateDoorUseCase, GetDoorUseCase, GetDoorByNameUseCase, GetDoorsByLocationUseCase,
    UpdateDoorUseCase, SetDoorStatusUseCase, ListDoorsUseCase, GetActiveDoorsUseCase,
    GetDoorsBySecurityLevelUseCase, DeleteDoorUseCase
)
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule
from app.domain.exceptions import DomainError, DoorNotFoundError, EntityAlreadyExistsError
from tests.conftest import SAMPLE_DOOR_UUID, SAMPLE_DOOR_UUID_2, SAMPLE_CARD_UUID, SAMPLE_CARD_UUID_2

class TestCreateDoorUseCase:
    """Test cases for CreateDoorUseCase"""
    
    @pytest.fixture
    def mock_door_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def create_door_use_case(self, mock_door_repository):
        return CreateDoorUseCase(mock_door_repository)
    
    @pytest.mark.asyncio
    async def test_create_door_success(self, create_door_use_case, mock_door_repository):
        """
        Verifies that a door can be successfully created when no door with the same name exists.
        
        Asserts that the created door has the expected properties and that the repository methods for checking name uniqueness and creating the door are called appropriately.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Mock door name doesn't exist
        mock_door_repository.get_by_name.return_value = None
        
        # Mock door creation
        expected_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            description="Main building entrance",
            requires_pin=False,
            max_attempts=3,
            lockout_duration=300,
            failed_attempts=0
        )
        mock_door_repository.create.return_value = expected_door
        
        # Execute use case
        result = await create_door_use_case.execute(
            name="Main Entrance",
            location="Building A",
            door_type="entrance",
            security_level="medium",
            description="Main building entrance",
            requires_pin=False,
            max_attempts=3,
            lockout_duration=300
        )
        
        # Verify
        assert result.name == "Main Entrance"
        assert result.location == "Building A"
        assert result.door_type == DoorType.ENTRANCE
        assert result.security_level == SecurityLevel.MEDIUM
        mock_door_repository.get_by_name.assert_called_once_with("Main Entrance")
        mock_door_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_door_duplicate_name(self, create_door_use_case, mock_door_repository):
        """Test door creation fails when name already exists"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Mock door name already exists
        existing_door = Door(
            id=SAMPLE_DOOR_UUID_2,
            name="Main Entrance",
            location="Building B",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        mock_door_repository.get_by_name.return_value = existing_door
        
        # Execute and verify exception
        with pytest.raises(EntityAlreadyExistsError, match="Door with identifier 'Main Entrance' already exists"):
            await create_door_use_case.execute(
                name="Main Entrance",
                location="Building A",
                door_type="entrance",
                security_level="medium"
            )
        
        mock_door_repository.get_by_name.assert_called_once_with("Main Entrance")
        mock_door_repository.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_door_with_schedule(self, create_door_use_case, mock_door_repository):
        """
        Tests that a door can be created with an access schedule.
        
        Verifies that when a new door is created with schedule data, the resulting door includes the specified access schedule and the repository's create method is called.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        
        # Mock door name doesn't exist
        mock_door_repository.get_by_name.return_value = None
        
        # Create expected door with schedule
        schedule = AccessSchedule(
            days_of_week=[0, 1, 2, 3, 4],
            start_time=time(9, 0),
            end_time=time(18, 0)
        )
        expected_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Office Door",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            default_schedule=schedule
        )
        mock_door_repository.create.return_value = expected_door
        
        # Execute use case with schedule data
        schedule_data = {
            'days_of_week': [0, 1, 2, 3, 4],
            'start_time': '09:00',
            'end_time': '18:00'
        }
        
        result = await create_door_use_case.execute(
            name="Office Door",
            location="Building A",
            door_type="entrance",
            security_level="medium",
            default_schedule_data=schedule_data
        )
        
        # Verify
        assert result.name == "Office Door"
        assert result.default_schedule is not None
        mock_door_repository.create.assert_called_once()

class TestGetDoorUseCase:
    """Test cases for GetDoorUseCase"""
    
    @pytest.fixture
    def mock_door_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def get_door_use_case(self, mock_door_repository):
        return GetDoorUseCase(mock_door_repository)
    
    @pytest.mark.asyncio
    async def test_get_door_success(self, get_door_use_case, mock_door_repository):
        """
        Verifies that a door can be successfully retrieved by its identifier using the GetDoorUseCase.
        
        Asserts that the returned door matches the expected entity and that the repository is called with the correct identifier.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        expected_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        mock_door_repository.get_by_id.return_value = expected_door
        
        result = await get_door_use_case.execute(SAMPLE_DOOR_UUID)
        
        assert result == expected_door
        mock_door_repository.get_by_id.assert_called_once_with(SAMPLE_DOOR_UUID)
    
    @pytest.mark.asyncio
    async def test_get_door_not_found(self, get_door_use_case, mock_door_repository):
        """
        Tests that retrieving a non-existent door by identifier raises DoorNotFoundError.
        """
        mock_door_repository.get_by_id.return_value = None
        
        with pytest.raises(DoorNotFoundError, match="Door with identifier '999' not found"):
            await get_door_use_case.execute(999)
        
        mock_door_repository.get_by_id.assert_called_once_with(999)

class TestUpdateDoorUseCase:
    """Test cases for UpdateDoorUseCase"""
    
    @pytest.fixture
    def mock_door_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def update_door_use_case(self, mock_door_repository):
        return UpdateDoorUseCase(mock_door_repository)
    
    @pytest.mark.asyncio
    async def test_update_door_success(self, update_door_use_case, mock_door_repository):
        """
        Tests that updating a door with valid data succeeds and returns the updated door entity.
        
        Verifies that the door repository is called to fetch the original door, checks for name conflicts, and updates the door with new details. Asserts that the returned door reflects the updated name and security level.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        original_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        updated_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance - Updated",  # Updated
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.HIGH,  # Updated
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now + timedelta(minutes=1)
        )
        
        mock_door_repository.get_by_id.return_value = original_door
        mock_door_repository.get_by_name.return_value = None  # New name doesn't exist
        mock_door_repository.update.return_value = updated_door
        
        result = await update_door_use_case.execute(
            door_id=SAMPLE_DOOR_UUID,
            name="Main Entrance - Updated",
            security_level="high"
        )
        
        assert result.name == "Main Entrance - Updated"
        assert result.security_level == SecurityLevel.HIGH
        mock_door_repository.get_by_id.assert_called_once_with(SAMPLE_DOOR_UUID)
        mock_door_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_door_not_found(self, update_door_use_case, mock_door_repository):
        """
        Tests that updating a non-existent door raises a DoorNotFoundError and does not attempt an update.
        """
        mock_door_repository.get_by_id.return_value = None
        
        with pytest.raises(DoorNotFoundError, match="Door with identifier '999' not found"):
            await update_door_use_case.execute(door_id=999, name="New Name")
        
        mock_door_repository.get_by_id.assert_called_once_with(999)
        mock_door_repository.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_door_name_conflict(self, update_door_use_case, mock_door_repository):
        """
        Tests that updating a door fails with EntityAlreadyExistsError when the new name is already used by another door.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        original_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        conflicting_door = Door(
            id=SAMPLE_DOOR_UUID_2,
            name="Side Entrance",  # This name is already taken
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        mock_door_repository.get_by_id.return_value = original_door
        mock_door_repository.get_by_name.return_value = conflicting_door
        
        with pytest.raises(EntityAlreadyExistsError, match="Door with identifier 'Side Entrance' already exists"):
            await update_door_use_case.execute(door_id=SAMPLE_DOOR_UUID, name="Side Entrance")
        
        mock_door_repository.get_by_id.assert_called_once_with(SAMPLE_DOOR_UUID)
        mock_door_repository.get_by_name.assert_called_once_with("Side Entrance")
        mock_door_repository.update.assert_not_called()

class TestSetDoorStatusUseCase:
    """Test cases for SetDoorStatusUseCase"""
    
    @pytest.fixture
    def mock_door_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def set_door_status_use_case(self, mock_door_repository):
        return SetDoorStatusUseCase(mock_door_repository)
    
    @pytest.mark.asyncio
    async def test_set_door_status_active(self, set_door_status_use_case, mock_door_repository):
        """Test setting door status to active"""
        now = datetime.now(UTC).replace(tzinfo=None)
        original_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.MAINTENANCE,
            created_at=now,
            updated_at=now,
            failed_attempts=3,
            locked_until=now + timedelta(minutes=5)
        )
        
        # Simulate door being activated (domain logic resets failed attempts)
        activated_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,  # Updated
            created_at=now,
            updated_at=now + timedelta(minutes=1),
            failed_attempts=0,  # Reset by domain logic
            locked_until=None  # Reset by domain logic
        )
        
        mock_door_repository.get_by_id.return_value = original_door
        mock_door_repository.update.return_value = activated_door
        
        result = await set_door_status_use_case.execute(SAMPLE_DOOR_UUID, "active")
        
        assert result.status == DoorStatus.ACTIVE
        assert result.failed_attempts == 0
        assert result.locked_until is None
        mock_door_repository.get_by_id.assert_called_once_with(SAMPLE_DOOR_UUID)
        mock_door_repository.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_door_status_emergency_open(self, set_door_status_use_case, mock_door_repository):
        """
        Tests that setting a door's status to emergency open updates the status correctly.
        
        Verifies that the use case retrieves the door, updates its status to emergency open, and persists the change in the repository.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        original_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        emergency_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.EMERGENCY_OPEN,  # Updated
            created_at=now,
            updated_at=now + timedelta(minutes=1)
        )
        
        mock_door_repository.get_by_id.return_value = original_door
        mock_door_repository.update.return_value = emergency_door
        
        result = await set_door_status_use_case.execute(SAMPLE_DOOR_UUID, "emergency_open")
        
        assert result.status == DoorStatus.EMERGENCY_OPEN
        mock_door_repository.get_by_id.assert_called_once_with(SAMPLE_DOOR_UUID)
        mock_door_repository.update.assert_called_once()

class TestListDoorsUseCase:
    """Test cases for ListDoorsUseCase"""
    
    @pytest.fixture
    def mock_door_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def list_doors_use_case(self, mock_door_repository):
        return ListDoorsUseCase(mock_door_repository)
    
    @pytest.mark.asyncio
    async def test_list_doors_success(self, list_doors_use_case, mock_door_repository):
        """
        Tests that listing doors returns the expected list of door entities.
        
        Verifies that the use case retrieves the correct number of doors with expected names and that the repository is called with the correct pagination parameters.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        doors = [
            Door(
                id=SAMPLE_DOOR_UUID,
                name="Main Entrance",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.MEDIUM,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now
            ),
            Door(
                id=SAMPLE_DOOR_UUID_2,
                name="Side Entrance",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.LOW,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now
            )
        ]
        
        mock_door_repository.list_doors.return_value = doors
        
        result = await list_doors_use_case.execute(skip=0, limit=10)
        
        assert len(result) == 2
        assert result[0].name == "Main Entrance"
        assert result[1].name == "Side Entrance"
        mock_door_repository.list_doors.assert_called_once_with(0, 10)

class TestGetActiveDoorsUseCase:
    """Test cases for GetActiveDoorsUseCase"""
    
    @pytest.fixture
    def mock_door_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def get_active_doors_use_case(self, mock_door_repository):
        return GetActiveDoorsUseCase(mock_door_repository)
    
    @pytest.mark.asyncio
    async def test_get_active_doors_success(self, get_active_doors_use_case, mock_door_repository):
        """
        Tests that active doors are successfully retrieved using the GetActiveDoorsUseCase.
        
        Asserts that the returned list contains only doors with active status and verifies the repository method is called once.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        active_doors = [
            Door(
                id=SAMPLE_DOOR_UUID,
                name="Main Entrance",
                location="Building A",
                door_type=DoorType.ENTRANCE,
                security_level=SecurityLevel.MEDIUM,
                status=DoorStatus.ACTIVE,
                created_at=now,
                updated_at=now
            )
        ]
        
        mock_door_repository.get_active_doors.return_value = active_doors
        
        result = await get_active_doors_use_case.execute()
        
        assert len(result) == 1
        assert result[0].status == DoorStatus.ACTIVE
        mock_door_repository.get_active_doors.assert_called_once()

class TestDeleteDoorUseCase:
    """Test cases for DeleteDoorUseCase"""
    
    @pytest.fixture
    def mock_door_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def delete_door_use_case(self, mock_door_repository):
        return DeleteDoorUseCase(mock_door_repository)
    
    @pytest.mark.asyncio
    async def test_delete_door_success(self, delete_door_use_case, mock_door_repository):
        """
        Tests that a door is successfully deleted when it exists in the repository.
        
        Verifies that the delete operation returns True and that the repository's get and delete methods are called with the correct identifier.
        """
        now = datetime.now(UTC).replace(tzinfo=None)
        existing_door = Door(
            id=SAMPLE_DOOR_UUID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        mock_door_repository.get_by_id.return_value = existing_door
        mock_door_repository.delete.return_value = True
        
        result = await delete_door_use_case.execute(SAMPLE_DOOR_UUID)
        
        assert result is True
        mock_door_repository.get_by_id.assert_called_once_with(SAMPLE_DOOR_UUID)
        mock_door_repository.delete.assert_called_once_with(SAMPLE_DOOR_UUID)
    
    @pytest.mark.asyncio
    async def test_delete_door_not_found(self, delete_door_use_case, mock_door_repository):
        """
        Tests that deleting a non-existent door raises a DoorNotFoundError and does not call the delete method.
        """
        mock_door_repository.get_by_id.return_value = None
        
        with pytest.raises(DoorNotFoundError, match="Door with identifier .* not found"):
            await delete_door_use_case.execute(SAMPLE_DOOR_UUID)
        
        mock_door_repository.get_by_id.assert_called_once_with(SAMPLE_DOOR_UUID)
        mock_door_repository.delete.assert_not_called()