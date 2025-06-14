"""
Integration tests for access validation API.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, UTC, time
from uuid import UUID

from app.domain.entities.card import Card, CardType, CardStatus
from app.domain.entities.door import Door, DoorStatus, SecurityLevel, DoorType, AccessSchedule
from app.domain.entities.user import User, Role, UserStatus
from app.domain.entities.permission import Permission, PermissionStatus
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_DOOR_UUID, SAMPLE_ADMIN_UUID


class TestAccessValidationAPI:
    """Integration tests for access validation API."""
    
    @pytest.fixture
    def client(self):
        """HTTP client for testing."""
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin_user(self):
        """Mock admin user for testing."""
        return User(
            id=SAMPLE_ADMIN_UUID,
            email="admin@test.com",
            hashed_password="hashed_password",
            full_name="Admin User",
            roles=[Role.ADMIN],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
    
    def setup_auth_override(self, client, user):
        """Helper to setup authentication override."""
        from app.api.dependencies.auth_dependencies import get_current_active_user
        client.app.dependency_overrides[get_current_active_user] = lambda: user
        
    def cleanup_overrides(self, client):
        """Helper to cleanup dependency overrides."""
        client.app.dependency_overrides.clear()

    def test_validate_access_success(self, client, mock_admin_user):
        """Test successful access validation"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock successful access validation
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=True,
                reason="Access granted for Test User",
                door_name="Main Entrance",
                user_name="Test User",
                card_type="employee",
                requires_pin=False,
                card_id="CARD001",
                door_id=SAMPLE_DOOR_UUID,
                user_id=SAMPLE_USER_UUID
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request
            request_data = {
                "card_id": "CARD001",
                "door_id": str(SAMPLE_DOOR_UUID),
                "device_id": "DEVICE001"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is True
                assert data["reason"] == "Access granted for Test User"
                assert data["requires_pin"] is False
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_card_not_found(self, client, mock_admin_user):
        """Test access validation when card is not found"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock card not found result
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=False,
                reason="Card not found",
                door_name="Main Entrance",
                card_type="unknown",
                requires_pin=False,
                card_id="INVALID_CARD",
                door_id=SAMPLE_DOOR_UUID,
                user_id=None
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request
            request_data = {
                "card_id": "INVALID_CARD",
                "door_id": str(SAMPLE_DOOR_UUID),
                "device_id": "DEVICE001"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is False
                assert data["reason"] == "Card not found"
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_door_not_found(self, client, mock_admin_user):
        """Test access validation when door is not found"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock door not found result
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=False,
                reason="Door not found",
                door_name="Unknown Door",
                card_type="employee",
                requires_pin=False,
                card_id="CARD001",
                door_id=SAMPLE_DOOR_UUID,
                user_id=SAMPLE_USER_UUID
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request
            request_data = {
                "card_id": "CARD001",
                "door_id": "invalid-door-uuid",
                "device_id": "DEVICE001"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is False
                assert data["reason"] == "Door not found"
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_no_permission(self, client, mock_admin_user):
        """Test access validation when user has no permission"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock no permission result
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=False,
                reason="No permission for this door",
                door_name="Main Entrance",
                user_name="Test User",
                card_type="employee",
                requires_pin=False,
                card_id="CARD001",
                door_id=SAMPLE_DOOR_UUID,
                user_id=SAMPLE_USER_UUID
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request
            request_data = {
                "card_id": "CARD001",
                "door_id": str(SAMPLE_DOOR_UUID),
                "device_id": "DEVICE001"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is False
                assert data["reason"] == "No permission for this door"
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_with_pin(self, client, mock_admin_user):
        """Test access validation that requires PIN"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock PIN required result
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=True,
                reason="Access granted with PIN",
                door_name="High Security Room",
                user_name="Test User",
                card_type="employee",
                requires_pin=True,
                card_id="CARD001",
                door_id=SAMPLE_DOOR_UUID,
                user_id=SAMPLE_USER_UUID
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request with PIN
            request_data = {
                "card_id": "CARD001",
                "door_id": str(SAMPLE_DOOR_UUID),
                "device_id": "DEVICE001",
                "pin": "1234"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is True
                assert data["requires_pin"] is True
                assert data["reason"] == "Access granted with PIN"
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_suspended_card(self, client, mock_admin_user):
        """Test access validation with suspended card"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock suspended card result
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=False,
                reason="Card is suspended",
                door_name="Main Entrance",
                user_name="Test User",
                card_type="employee",
                requires_pin=False,
                card_id="CARD001",
                door_id=SAMPLE_DOOR_UUID,
                user_id=SAMPLE_USER_UUID
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request
            request_data = {
                "card_id": "CARD001",
                "door_id": str(SAMPLE_DOOR_UUID),
                "device_id": "DEVICE001"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is False
                assert data["reason"] == "Card is suspended"
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_inactive_door(self, client, mock_admin_user):
        """Test access validation with inactive door"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock inactive door result
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=False,
                reason="Door is not accessible",
                door_name="Maintenance Room",
                user_name="Test User",
                card_type="employee",
                requires_pin=False,
                card_id="CARD001",
                door_id=SAMPLE_DOOR_UUID,
                user_id=SAMPLE_USER_UUID
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request
            request_data = {
                "card_id": "CARD001",
                "door_id": str(SAMPLE_DOOR_UUID),
                "device_id": "DEVICE001"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is False
                assert data["reason"] == "Door is not accessible"
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_master_card(self, client, mock_admin_user):
        """Test access validation with master card"""
        with patch('app.api.v1.access.ValidateAccessUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            
            # Mock master card result
            from app.api.schemas.access_schemas import AccessValidationResult
            mock_result = AccessValidationResult(
                access_granted=True,
                reason="Master card access granted",
                door_name="Main Entrance",
                user_name="Master User",
                card_type="master",
                requires_pin=False,
                card_id="MASTER001",
                door_id=SAMPLE_DOOR_UUID,
                user_id=SAMPLE_USER_UUID
            )
            mock_use_case.execute.return_value = mock_result
            
            # Make request
            request_data = {
                "card_id": "MASTER001",
                "door_id": str(SAMPLE_DOOR_UUID),
                "device_id": "DEVICE001"
            }
            
            try:
                response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["access_granted"] is True
                assert data["reason"] == "Master card access granted"
            finally:
                self.cleanup_overrides(client)

    def test_validate_access_invalid_request_format(self, client, mock_admin_user):
        """Test access validation with invalid request format"""
        # Setup authentication
        self.setup_auth_override(client, mock_admin_user)
        
        try:
            # Make request with missing required fields
            request_data = {
                "card_id": "",  # Empty card_id should fail validation
                "door_id": "invalid-uuid",  # Invalid UUID format
                # Missing device_id
            }
            
            response = client.post("/api/v1/access/validate", json=request_data, headers={"Authorization": "Bearer fake_token"})
            
            # Verify validation error
            assert response.status_code == 422
        finally:
            self.cleanup_overrides(client)