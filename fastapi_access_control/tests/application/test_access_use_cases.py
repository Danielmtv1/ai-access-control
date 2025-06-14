"""
Tests for access validation use cases.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, time
from uuid import uuid4, UUID

# Test UUIDs for consistent test data
TEST_USER_ID_1 = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
TEST_CARD_ID_1 = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d481")
TEST_CARD_ID_2 = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d482")
TEST_DOOR_ID_1 = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d483")
TEST_DOOR_ID_2 = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d484")
TEST_PERMISSION_ID_1 = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d485")

from app.application.use_cases.access_use_cases import ValidateAccessUseCase
from app.api.schemas.access_schemas import AccessValidationResult
from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.door import Door, DoorStatus, SecurityLevel, DoorType
from app.domain.entities.user import User, Role, UserStatus
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_CARD_UUID_2, SAMPLE_DOOR_UUID, SAMPLE_DOOR_UUID_2
from app.domain.entities.permission import Permission, PermissionStatus
from app.domain.services.device_communication_service import DeviceCommunicationService
from app.domain.entities.device_message import DeviceAccessResponse, DoorAction
from app.domain.exceptions import (
    EntityNotFoundError,
    CardNotFoundError,
    DoorNotFoundError,
    UserNotFoundError,
    InvalidCardError,
    InvalidDoorError,
    AccessDeniedError
)


class TestValidateAccessUseCase:
    """Test suite for ValidateAccessUseCase."""
    
    @pytest.fixture
    def mock_card_repository(self):
        """
        Creates and returns a mocked asynchronous card repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_door_repository(self):
        """
        Provides a mocked asynchronous door repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_permission_repository(self):
        """
        Creates and returns a mock asynchronous permission repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_user_repository(self):
        """
        Creates and returns a mocked asynchronous user repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_mqtt_service(self):
        """
        Creates and returns a mocked asynchronous MQTT service for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_device_communication_service(self):
        """
        Creates a mock asynchronous device communication service for testing.
        
        The returned mock service simulates publishing access responses and sending unlock or lock commands, always returning True for these operations.
        """
        service = AsyncMock(spec=DeviceCommunicationService)
        service.publish_access_response = AsyncMock(return_value=True)
        service.send_unlock_command = AsyncMock(return_value=True)
        service.send_lock_command = AsyncMock(return_value=True)
        return service
    
    @pytest.fixture
    def use_case(self, mock_card_repository, mock_door_repository, 
                 mock_permission_repository, mock_user_repository, mock_mqtt_service):
        """
                 Creates a ValidateAccessUseCase instance without device communication.
                 
                 Returns:
                     A ValidateAccessUseCase configured with the provided repositories and MQTT service.
                 """
        return ValidateAccessUseCase(
            card_repository=mock_card_repository,
            door_repository=mock_door_repository,
            permission_repository=mock_permission_repository,
            user_repository=mock_user_repository,
            mqtt_service=mock_mqtt_service
        )
    
    @pytest.fixture
    def use_case_with_device_service(self, mock_card_repository, mock_door_repository, 
                                   mock_permission_repository, mock_user_repository, 
                                   mock_mqtt_service, mock_device_communication_service):
        """
                                   Creates a ValidateAccessUseCase instance configured with device communication support.
                                   
                                   Returns:
                                       A ValidateAccessUseCase initialized with the provided repositories, MQTT service, and device communication service.
                                   """
        return ValidateAccessUseCase(
            card_repository=mock_card_repository,
            door_repository=mock_door_repository,
            permission_repository=mock_permission_repository,
            user_repository=mock_user_repository,
            mqtt_service=mock_mqtt_service,
            device_communication_service=mock_device_communication_service
        )
    
    @pytest.fixture
    def sample_card(self):
        """
        Creates and returns a sample active employee card for testing purposes.
        
        Returns:
            Card: An active card instance with preset attributes for use in tests.
        """
        return Card(
            id=TEST_CARD_ID_1,
            user_id=TEST_USER_ID_1,
            card_id="TEST123",
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=datetime.now(),
            valid_until=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            use_count=0,
            last_used=None
        )
    
    @pytest.fixture
    def sample_door(self):
        """
        Creates and returns a sample Door instance representing an active, accessible door for testing purposes.
        """
        return Door(
            id=TEST_DOOR_ID_1,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Main building entrance",
            default_schedule=None,
            requires_pin=False,
            max_attempts=3,
            lockout_duration=300,
            last_access=None,
            failed_attempts=0,
            locked_until=None
        )
    
    @pytest.fixture
    def sample_user(self):
        """
        Creates and returns a sample active user entity for testing purposes.
        
        Returns:
            User: An instance representing an active user with predefined attributes.
        """
        return User(
            id=TEST_USER_ID_1,
            email="test@company.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_login=None
        )
    
    @pytest.fixture
    def sample_permission(self):
        """
        Creates and returns a sample active permission entity for testing purposes.
        
        Returns:
            Permission: An active permission instance with preset attributes for user, door, validity period, and access schedule.
        """
        return Permission(
            id=TEST_PERMISSION_ID_1,
            user_id=TEST_USER_ID_1,
            door_id=TEST_DOOR_ID_1,
            status=PermissionStatus.ACTIVE,
            valid_from=datetime.now(),
            created_by=TEST_USER_ID_1,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            card_id=None,
            valid_until=datetime.now().replace(hour=18, minute=0, second=0, microsecond=0),
            access_schedule='{"days": ["mon", "tue", "wed", "thu", "fri"], "start": "08:00", "end": "18:00"}',
            pin_required=False,
            last_used=None
        )
    
    @pytest.mark.asyncio
    async def test_validate_access_card_not_found(self, use_case, mock_card_repository):
        """
        Tests that validating access raises CardNotFoundError when the card does not exist.
        """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = None
        
        # Act & Assert
        with pytest.raises(CardNotFoundError, match="Card with identifier 'TEST123' not found"):
            await use_case.execute("TEST123", TEST_DOOR_ID_1)
    
    @pytest.mark.asyncio
    async def test_validate_access_card_inactive(self, use_case, mock_card_repository, sample_card):
        """
        Tests that access validation raises InvalidCardError when the card is inactive.
        """
        # Arrange
        sample_card.status = CardStatus.SUSPENDED
        mock_card_repository.get_by_card_id.return_value = sample_card
        
        # Act & Assert
        with pytest.raises(InvalidCardError, match="Card TEST123 is inactive"):
            await use_case.execute("TEST123", TEST_DOOR_ID_1)
    
    @pytest.mark.asyncio
    async def test_validate_access_door_not_found(self, use_case, mock_card_repository, 
                                                   mock_door_repository, sample_card):
        """
                                                   Tests that DoorNotFoundError is raised when the specified door does not exist during access validation.
                                                   """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(DoorNotFoundError, match="Door with identifier '1' not found"):
            await use_case.execute("TEST123", 1)
    
    @pytest.mark.asyncio
    async def test_validate_access_door_not_accessible(self, use_case, mock_card_repository,
                                                        mock_door_repository, sample_card, sample_door):
        """
                                                        Tests that access validation raises InvalidDoorError when the door is not accessible.
                                                        """
        # Arrange
        sample_door.status = DoorStatus.MAINTENANCE
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        
        # Act & Assert
        with pytest.raises(InvalidDoorError, match="not accessible"):
            await use_case.execute("TEST123", TEST_DOOR_ID_1)
    
    @pytest.mark.asyncio
    async def test_validate_access_user_not_found(self, use_case, mock_card_repository,
                                                   mock_door_repository, mock_user_repository,
                                                   sample_card, sample_door):
        """
                                                   Tests that access validation raises UserNotFoundError when the user associated with the card does not exist.
                                                   """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(UserNotFoundError, match="User for card TEST123 not found"):
            await use_case.execute("TEST123", TEST_DOOR_ID_1)
    
    @pytest.mark.asyncio
    async def test_validate_access_user_inactive(self, use_case, mock_card_repository,
                                                  mock_door_repository, mock_user_repository,
                                                  sample_card, sample_door, sample_user):
        """Test validation when user is inactive."""
        # Arrange
        sample_user.status = UserStatus.INACTIVE
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        
        # Act & Assert
        with pytest.raises(InvalidCardError, match="User .* is inactive"):
            await use_case.execute("TEST123", TEST_DOOR_ID_1)
    
    @pytest.mark.asyncio
    async def test_validate_access_master_card_success(self, use_case, mock_card_repository,
                                                        mock_door_repository, mock_user_repository,
                                                        sample_card, sample_door, sample_user):
        """
                                                        Tests that access is granted when a master card is used, returning the correct result details.
                                                        """
        # Arrange
        sample_card.card_type = CardType.MASTER
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_card_repository.update.return_value = sample_card
        mock_door_repository.update.return_value = sample_door
        
        # Act
        result = await use_case.execute("TEST123", TEST_DOOR_ID_1)
        
        # Assert
        assert result.access_granted is True
        assert result.card_type == "master"
        assert "Master card access granted" in result.reason
        assert result.door_name == "Main Entrance"
        assert result.user_name == "Test User"
    
    @pytest.mark.asyncio
    async def test_validate_access_no_permission(self, use_case, mock_card_repository,
                                                  mock_door_repository, mock_user_repository,
                                                  mock_permission_repository,
                                                  sample_card, sample_door, sample_user):
        """
                                                  Tests that access validation raises AccessDeniedError when the user lacks permission for the door.
                                                  """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = False
        
        # Act & Assert
        with pytest.raises(AccessDeniedError, match="does not have permission"):
            await use_case.execute("TEST123", TEST_DOOR_ID_1)
    
    @pytest.mark.asyncio
    async def test_validate_access_success_with_permission(self, use_case, mock_card_repository,
                                                           mock_door_repository, mock_user_repository,
                                                           mock_permission_repository,
                                                           sample_card, sample_door, sample_user,
                                                           sample_permission):
        """
                                                           Tests that access is granted for a regular card with valid permission.
                                                           
                                                           Verifies that the use case returns an access granted result with correct card type, user, door, and permission details when all entities are valid and permission is present.
                                                           """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        mock_permission_repository.get_by_user_and_door.return_value = sample_permission
        mock_card_repository.update.return_value = sample_card
        mock_door_repository.update.return_value = sample_door
        
        # Act
        result = await use_case.execute("TEST123", TEST_DOOR_ID_1)
        
        # Assert
        assert result.access_granted is True
        assert result.card_type == "employee"
        assert "Access granted for Test User" in result.reason
        assert result.door_name == "Main Entrance"
        assert result.user_name == "Test User"
        assert result.valid_until == "18:00"
    
    @pytest.mark.asyncio
    async def test_validate_access_pin_required(self, use_case, mock_card_repository,
                                                 mock_door_repository, mock_user_repository,
                                                 mock_permission_repository,
                                                 sample_card, sample_door, sample_user):
        """
                                                 Tests that access validation denies entry and requires a PIN when a high-security door is accessed without a PIN.
                                                 
                                                 Ensures that the result indicates access is not granted, a PIN is required, and the denial reason includes a PIN requirement.
                                                 """
        # Arrange
        sample_door.security_level = SecurityLevel.CRITICAL
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        mock_permission_repository.get_by_user_and_door.return_value = None  # No permission for PIN test
        
        # Act
        result = await use_case.execute("TEST123", TEST_DOOR_ID_1)
        
        # Assert
        assert result.access_granted is False
        assert result.requires_pin is True
        assert "PIN required" in result.reason
    
    @pytest.mark.asyncio
    async def test_validate_access_invalid_pin(self, use_case, mock_card_repository,
                                                mock_door_repository, mock_user_repository,
                                                mock_permission_repository,
                                                sample_card, sample_door, sample_user):
        """
                                                Tests that access validation raises AccessDeniedError when an invalid PIN is provided for a high-security door.
                                                """
        # Arrange
        sample_door.security_level = SecurityLevel.HIGH
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        
        # Act & Assert
        with pytest.raises(AccessDeniedError, match="Invalid PIN"):
            await use_case.execute("TEST123", TEST_DOOR_ID_1, pin="abc")
    
    @pytest.mark.asyncio
    async def test_validate_access_valid_pin(self, use_case, mock_card_repository,
                                             mock_door_repository, mock_user_repository,
                                             mock_permission_repository,
                                             sample_card, sample_door, sample_user, sample_permission):
        """Test validation with valid PIN."""
        # Arrange
        sample_door.security_level = SecurityLevel.CRITICAL
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        mock_permission_repository.get_by_user_and_door.return_value = sample_permission
        mock_card_repository.update.return_value = sample_card
        mock_door_repository.update.return_value = sample_door
        
        # Act
        result = await use_case.execute("TEST123", TEST_DOOR_ID_1, pin="1234")
        
        # Assert
        assert result.access_granted is True
        assert result.requires_pin is True
        assert "Access granted" in result.reason
    
    @pytest.mark.asyncio
    async def test_log_access_attempt_called(self, use_case, mock_card_repository,
                                              mock_mqtt_service, sample_card):
        """
                                              Verifies that an access attempt is logged via MQTT when access is denied due to a missing card.
                                              
                                              Ensures the MQTT service records the attempt with the correct topic and payload reflecting the denied result.
                                              """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = None
        
        # Act
        try:
            await use_case.execute("TEST123", TEST_DOOR_ID_1)
        except EntityNotFoundError:
            pass
        
        # Assert
        assert mock_mqtt_service.save_message.call_count >= 1
        # Check the last call (most recent log)
        call_args = mock_mqtt_service.save_message.call_args[0][0]
        assert call_args.topic == f"access/door_{TEST_DOOR_ID_1}/attempts"
        import json
        payload = json.loads(call_args.message)
        assert payload["card_id"] == "TEST123"
        assert payload["result"] == "denied"


class TestValidateAccessUseCaseWithMqttDevicesCommunication:
    """Test suite for ValidateAccessUseCase with MQTT device communication."""
    
    @pytest.fixture
    def mock_card_repository(self):
        """
        Creates and returns a mocked asynchronous card repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_door_repository(self):
        """
        Provides a mocked asynchronous door repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_permission_repository(self):
        """
        Creates and returns a mock asynchronous permission repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_user_repository(self):
        """
        Creates and returns a mocked asynchronous user repository for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_mqtt_service(self):
        """
        Creates and returns a mocked asynchronous MQTT service for testing purposes.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_device_communication_service(self):
        """
        Creates a mock asynchronous device communication service for testing.
        
        The returned mock service simulates publishing access responses and sending unlock or lock commands, always returning True for these operations.
        """
        service = AsyncMock(spec=DeviceCommunicationService)
        service.publish_access_response = AsyncMock(return_value=True)
        service.send_unlock_command = AsyncMock(return_value=True)
        service.send_lock_command = AsyncMock(return_value=True)
        return service
    
    @pytest.fixture
    def use_case_with_devices(self, mock_card_repository, mock_door_repository, 
                            mock_permission_repository, mock_user_repository, 
                            mock_mqtt_service, mock_device_communication_service):
        """
                            Creates a ValidateAccessUseCase instance configured with device communication.
                            
                            Returns:
                                A ValidateAccessUseCase initialized with the provided repositories, MQTT service, and device communication service.
                            """
        return ValidateAccessUseCase(
            card_repository=mock_card_repository,
            door_repository=mock_door_repository,
            permission_repository=mock_permission_repository,
            user_repository=mock_user_repository,
            mqtt_service=mock_mqtt_service,
            device_communication_service=mock_device_communication_service
        )
    
    @pytest.fixture
    def sample_card(self):
        """
        Creates and returns a sample active employee card for testing purposes.
        
        Returns:
            Card: An active card instance with preset attributes for use in tests.
        """
        return Card(
            id=TEST_CARD_ID_1,
            user_id=TEST_USER_ID_1,
            card_id="TEST123",
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=datetime.now(),
            valid_until=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            use_count=0,
            last_used=None
        )
    
    @pytest.fixture
    def sample_master_card(self):
        """
        Returns a sample master card entity with active status for testing purposes.
        """
        return Card(
            id=TEST_CARD_ID_2,
            user_id=TEST_USER_ID_1,
            card_id="MASTER001",
            card_type=CardType.MASTER,
            status=CardStatus.ACTIVE,
            valid_from=datetime.now(),
            valid_until=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            use_count=0,
            last_used=None
        )
    
    @pytest.fixture
    def sample_door(self):
        """
        Creates and returns a sample Door instance representing an active, accessible door for testing purposes.
        """
        return Door(
            id=TEST_DOOR_ID_1,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Main building entrance",
            default_schedule=None,
            requires_pin=False,
            max_attempts=3,
            lockout_duration=300,
            last_access=None,
            failed_attempts=0,
            locked_until=None
        )
    
    @pytest.fixture
    def sample_critical_door(self):
        """
        Creates and returns a sample Door instance representing a critical security door requiring a PIN for access.
        """
        return Door(
            id=TEST_DOOR_ID_2,
            name="Server Room",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.CRITICAL,
            status=DoorStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description="Server room - high security",
            default_schedule=None,
            requires_pin=True,
            max_attempts=2,
            lockout_duration=600,
            last_access=None,
            failed_attempts=0,
            locked_until=None
        )
    
    @pytest.fixture
    def sample_user(self):
        """
        Creates and returns a sample active user entity for testing purposes.
        
        Returns:
            User: An instance representing an active user with predefined attributes.
        """
        return User(
            id=TEST_USER_ID_1,
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_login=None
        )
    
    @pytest.mark.asyncio
    async def test_access_granted_with_device_response(self, use_case_with_devices,
                                                     mock_card_repository, mock_door_repository,
                                                     mock_user_repository, mock_permission_repository,
                                                     mock_device_communication_service,
                                                     sample_card, sample_door, sample_user):
        """
                                                     Tests that access is granted when all conditions are met, and verifies that the device communication service sends both an access granted response and an unlock command to the specified device.
                                                     """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        mock_permission_repository.get_by_user_and_door.return_value = None
        mock_card_repository.update.return_value = sample_card
        mock_door_repository.update.return_value = sample_door
        
        device_id = "door_lock_001"
        
        # Act
        result = await use_case_with_devices.execute("TEST123", TEST_DOOR_ID_1, device_id=device_id)
        
        # Assert
        assert result.access_granted is True
        
        # Verify device response was sent
        mock_device_communication_service.publish_access_response.assert_called_once()
        call_args = mock_device_communication_service.publish_access_response.call_args
        assert call_args[0][0] == device_id  # device_id parameter
        
        response = call_args[0][1]  # DeviceAccessResponse object
        assert response.access_granted is True
        assert response.door_action == DoorAction.UNLOCK
        assert response.user_name == "Test User"
        assert response.card_type == "employee"
        
        # Verify unlock command was sent
        mock_device_communication_service.send_unlock_command.assert_called_once_with(device_id, duration=5)
    
    @pytest.mark.asyncio
    async def test_master_card_with_device_response(self, use_case_with_devices,
                                                  mock_card_repository, mock_door_repository,
                                                  mock_user_repository,
                                                  mock_device_communication_service,
                                                  sample_master_card, sample_door, sample_user):
        """
                                                  Tests that access is granted for a master card and verifies that the device communication
                                                  service sends both an access response and an unlock command to the device.
                                                  """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_master_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_card_repository.update.return_value = sample_master_card
        mock_door_repository.update.return_value = sample_door
        
        device_id = "door_lock_001"
        
        # Act
        result = await use_case_with_devices.execute("MASTER001", TEST_DOOR_ID_1, device_id=device_id)
        
        # Assert
        assert result.access_granted is True
        assert result.card_type == "master"
        
        # Verify device response was sent
        mock_device_communication_service.publish_access_response.assert_called_once()
        call_args = mock_device_communication_service.publish_access_response.call_args
        
        response = call_args[0][1]
        assert response.access_granted is True
        assert response.card_type == "master"
        assert "Master card access granted" in response.reason
        
        # Verify unlock command was sent
        mock_device_communication_service.send_unlock_command.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_access_denied_with_device_response(self, use_case_with_devices,
                                                    mock_card_repository, mock_door_repository,
                                                    mock_user_repository, mock_permission_repository,
                                                    mock_device_communication_service,
                                                    sample_card, sample_door, sample_user):
        """
                                                    Tests that access is denied when the user lacks permission, and verifies that a denial response is sent to the device without triggering an unlock command.
                                                    """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = False  # No permission
        
        device_id = "door_lock_001"
        
        # Act & Assert
        with pytest.raises(AccessDeniedError):
            await use_case_with_devices.execute("TEST123", TEST_DOOR_ID_1, device_id=device_id)
        
        # Verify denial response was sent
        mock_device_communication_service.publish_access_response.assert_called_once()
        call_args = mock_device_communication_service.publish_access_response.call_args
        
        response = call_args[0][1]
        assert response.access_granted is False
        assert response.door_action == DoorAction.DENY
        
        # Verify no unlock command was sent
        mock_device_communication_service.send_unlock_command.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_pin_required_with_device_response(self, use_case_with_devices,
                                                   mock_card_repository, mock_door_repository,
                                                   mock_user_repository, mock_permission_repository,
                                                   mock_device_communication_service,
                                                   sample_card, sample_critical_door, sample_user):
        """
                                                   Verifies that when a critical door requiring a PIN is accessed, the use case denies access and sends a device response indicating that a PIN is required, without sending an unlock command.
                                                   """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_critical_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        
        device_id = "door_lock_001"
        
        # Act
        result = await use_case_with_devices.execute("TEST123", TEST_DOOR_ID_2, device_id=device_id)
        
        # Assert
        assert result.access_granted is False
        assert result.requires_pin is True
        
        # Verify PIN required response was sent
        mock_device_communication_service.publish_access_response.assert_called_once()
        call_args = mock_device_communication_service.publish_access_response.call_args
        
        response = call_args[0][1]
        assert response.access_granted is False
        assert response.door_action == DoorAction.REQUIRE_PIN
        assert response.requires_pin is True
        
        # Verify no unlock command was sent
        mock_device_communication_service.send_unlock_command.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_card_not_found_with_device_response(self, use_case_with_devices,
                                                     mock_card_repository,
                                                     mock_device_communication_service):
        """
                                                     Tests that when a card is not found, an access denial response is sent to the device and an EntityNotFoundError is raised.
                                                     
                                                     Verifies that the device communication service publishes an access denial response with the appropriate reason.
                                                     """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = None
        device_id = "door_lock_001"
        
        # Act & Assert
        with pytest.raises(EntityNotFoundError):
            await use_case_with_devices.execute("INVALID123", TEST_DOOR_ID_1, device_id=device_id)
        
        # Verify denial response was sent
        mock_device_communication_service.publish_access_response.assert_called_once()
        call_args = mock_device_communication_service.publish_access_response.call_args
        
        response = call_args[0][1]
        assert response.access_granted is False
        assert "Card with identifier 'INVALID123' not found" in response.reason
    
    @pytest.mark.asyncio
    async def test_no_device_id_no_mqtt_response(self, use_case_with_devices,
                                                mock_card_repository, mock_door_repository,
                                                mock_user_repository, mock_permission_repository,
                                                mock_device_communication_service,
                                                sample_card, sample_door, sample_user):
        """
                                                Verifies that no device communication occurs when validating access without a device ID.
                                                
                                                Ensures that access is granted and no MQTT responses or unlock commands are sent when the device ID is not provided during access validation.
                                                """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        mock_permission_repository.get_by_user_and_door.return_value = None
        mock_card_repository.update.return_value = sample_card
        mock_door_repository.update.return_value = sample_door
        
        # Act (no device_id provided)
        result = await use_case_with_devices.execute("TEST123", TEST_DOOR_ID_1)
        
        # Assert
        assert result.access_granted is True
        
        # Verify no device communication occurred
        mock_device_communication_service.publish_access_response.assert_not_called()
        mock_device_communication_service.send_unlock_command.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_device_communication_failure_handling(self, use_case_with_devices,
                                                        mock_card_repository, mock_door_repository,
                                                        mock_user_repository, mock_permission_repository,
                                                        mock_device_communication_service,
                                                        sample_card, sample_door, sample_user):
        """
                                                        Tests that access validation succeeds even if device communication methods raise exceptions.
                                                        
                                                        Simulates failures in device communication during access validation and verifies that such failures do not prevent access from being granted. Ensures that the use case attempts to communicate with the device, but exceptions in these methods do not propagate or affect the result.
                                                        """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        mock_permission_repository.get_by_user_and_door.return_value = None
        mock_card_repository.update.return_value = sample_card
        mock_door_repository.update.return_value = sample_door
        
        # Make device communication fail
        mock_device_communication_service.publish_access_response.side_effect = Exception("MQTT error")
        mock_device_communication_service.send_unlock_command.side_effect = Exception("MQTT error")
        
        device_id = "door_lock_001"
        
        # Act - should not raise exception despite MQTT failures
        result = await use_case_with_devices.execute("TEST123", TEST_DOOR_ID_1, device_id=device_id)
        
        # Assert - access validation should still succeed
        assert result.access_granted is True
        
        # Verify attempt was made to communicate with device
        # Note: Since publish_access_response fails, send_unlock_command is never called
        mock_device_communication_service.publish_access_response.assert_called_once()
        mock_device_communication_service.send_unlock_command.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_access_with_pin_and_device_response(self, use_case_with_devices,
                                                     mock_card_repository, mock_door_repository,
                                                     mock_user_repository, mock_permission_repository,
                                                     mock_device_communication_service,
                                                     sample_card, sample_critical_door, sample_user):
        """
                                                     Tests that access is granted with a valid PIN for a critical door, and verifies that the device communication service sends both an access response and an unlock command to the device.
                                                     """
        # Arrange
        mock_card_repository.get_by_card_id.return_value = sample_card
        mock_door_repository.get_by_id.return_value = sample_critical_door
        mock_user_repository.get_by_id.return_value = sample_user
        mock_permission_repository.check_access.return_value = True
        mock_permission_repository.get_by_user_and_door.return_value = None
        mock_card_repository.update.return_value = sample_card
        mock_door_repository.update.return_value = sample_critical_door
        
        device_id = "door_lock_001"
        
        # Act
        result = await use_case_with_devices.execute("TEST123", TEST_DOOR_ID_2, pin="1234", device_id=device_id)
        
        # Assert
        assert result.access_granted is True
        
        # Verify device response was sent
        mock_device_communication_service.publish_access_response.assert_called_once()
        call_args = mock_device_communication_service.publish_access_response.call_args
        
        response = call_args[0][1]
        assert response.access_granted is True
        assert response.door_action == DoorAction.UNLOCK
        
        # Verify unlock command was sent
        mock_device_communication_service.send_unlock_command.assert_called_once_with(device_id, duration=5)