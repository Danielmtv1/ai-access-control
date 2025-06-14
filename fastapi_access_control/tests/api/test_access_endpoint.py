"""
Tests for access validation API endpoint.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.api.v1.access import validate_access, get_card_repository, get_door_repository
from app.api.schemas.access_schemas import AccessValidationRequest, AccessValidationResponse
from app.domain.exceptions import EntityNotFoundError, InvalidCardError, AccessDeniedError
from uuid import UUID

class TestAccessEndpoint:
    """Test suite for access validation endpoint."""
    TEST_DOOR_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d483")
    TEST_USER_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
    
    @pytest.fixture
    def client(self):
        """HTTP test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_validate_use_case(self):
        """Mock ValidateAccessUseCase."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repository dependencies."""
        return {
            'card_repository': AsyncMock(),
            'door_repository': AsyncMock(),
            'permission_repository': AsyncMock(),
            'user_repository': AsyncMock(),
            'mqtt_service': AsyncMock()
        }
    
    def test_validate_access_endpoint_exists(self, client):
        """Test that access validation endpoint exists."""
        # This should return 422 (validation error) or other error, not 404
        response = client.post("/api/v1/access/validate", json={})
        assert response.status_code != 404
    
    def test_validate_access_request_validation(self, client):
        """Test request validation for access endpoint."""
        # Test missing required fields
        response = client.post("/api/v1/access/validate", json={})
        assert response.status_code == 422
        
        # Test invalid data types
        response = client.post("/api/v1/access/validate", json={
            "card_id": 123,  # Should be string
            "door_id": "abc"  # Should be integer
        })
        assert response.status_code == 422
        
        # Test invalid door_id (must be positive)
        response = client.post("/api/v1/access/validate", json={
            "card_id": "TEST123",
            "door_id": -1
        })
        assert response.status_code == 422
    
    def test_validate_access_card_id_validation(self, client):
        """Test card_id field validation."""
        # Test empty card_id
        response = client.post("/api/v1/access/validate", json={
            "card_id": "",
            "door_id": self.TEST_DOOR_ID
        })
        assert response.status_code == 422
        
        # Test card_id too long
        response = client.post("/api/v1/access/validate", json={
            "card_id": "X" * 51,  # Max 50 characters
            "door_id": self.TEST_DOOR_ID
        })
        assert response.status_code == 422
    
    def test_validate_access_pin_validation(self, client):
        """Test PIN field validation."""
        # Test PIN too short
        response = client.post("/api/v1/access/validate", json={
            "card_id": "TEST123",
            "door_id": self.TEST_DOOR_ID,
            "pin": "123"  # Too short
        })
        assert response.status_code == 422
        
        # Test PIN too long
        response = client.post("/api/v1/access/validate", json={
            "card_id": "TEST123",
            "door_id": self.TEST_DOOR_ID,
            "pin": "123456789"  # Too long
        })
        assert response.status_code == 422
    
    @patch('app.api.v1.access.ValidateAccessUseCase')
    def test_validate_access_success(self, mock_use_case_class, client, mock_repositories):
        """Test successful access validation."""
        # Arrange
        mock_use_case = AsyncMock()
        mock_use_case_class.return_value = mock_use_case
        
        from app.api.schemas.access_schemas import AccessValidationResult
        mock_result = AccessValidationResult(
            access_granted=True,
            reason="Access granted for Test User",
            door_name="Test Door",
            user_name="Test User",
            card_type="employee",
            requires_pin=False,
            card_id="TEST123",
            door_id=SAMPLE_CARD_UUID,
            user_id=SAMPLE_CARD_UUID
        )
        mock_use_case.execute.return_value = mock_result
        
        # Mock all dependencies
        with patch.multiple(
            'app.api.v1.access',
            get_card_repository=AsyncMock(return_value=mock_repositories['card_repository']),
            get_door_repository=AsyncMock(return_value=mock_repositories['door_repository']),
            get_permission_repository=AsyncMock(return_value=mock_repositories['permission_repository']),
            get_user_repository=AsyncMock(return_value=mock_repositories['user_repository']),
            get_mqtt_service=AsyncMock(return_value=mock_repositories['mqtt_service'])
        ):
            # Act
            response = client.post("/api/v1/access/validate", json={
                "card_id": "TEST123",
                "door_id": self.TEST_DOOR_ID
            })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["door_name"] == "Test Door"
        assert data["user_name"] == "Test User"
        assert data["card_type"] == "employee"
        assert "timestamp" in data
    
    @patch('app.api.v1.access.ValidateAccessUseCase')
    def test_validate_access_card_not_found(self, mock_use_case_class, client, mock_repositories):
        """Test access validation with card not found."""
        # Arrange
        mock_use_case = AsyncMock()
        mock_use_case_class.return_value = mock_use_case
        mock_use_case.execute.side_effect = EntityNotFoundError("Card TEST123 not found")
        
        # Mock all dependencies
        with patch.multiple(
            'app.api.v1.access',
            get_card_repository=AsyncMock(return_value=mock_repositories['card_repository']),
            get_door_repository=AsyncMock(return_value=mock_repositories['door_repository']),
            get_permission_repository=AsyncMock(return_value=mock_repositories['permission_repository']),
            get_user_repository=AsyncMock(return_value=mock_repositories['user_repository']),
            get_mqtt_service=AsyncMock(return_value=mock_repositories['mqtt_service'])
        ):
            # Act
            response = client.post("/api/v1/access/validate", json={
                "card_id": "TEST123",
                "door_id": self.TEST_DOOR_ID
            })
        
        # Assert
        assert response.status_code == 404
        assert "Card TEST123 not found" in response.json()["detail"]
    
    @patch('app.api.v1.access.ValidateAccessUseCase')
    def test_validate_access_invalid_card(self, mock_use_case_class, client, mock_repositories):
        """Test access validation with invalid card."""
        # Arrange
        mock_use_case = AsyncMock()
        mock_use_case_class.return_value = mock_use_case
        mock_use_case.execute.side_effect = InvalidCardError("Card TEST123 is inactive")
        
        # Mock all dependencies
        with patch.multiple(
            'app.api.v1.access',
            get_card_repository=AsyncMock(return_value=mock_repositories['card_repository']),
            get_door_repository=AsyncMock(return_value=mock_repositories['door_repository']),
            get_permission_repository=AsyncMock(return_value=mock_repositories['permission_repository']),
            get_user_repository=AsyncMock(return_value=mock_repositories['user_repository']),
            get_mqtt_service=AsyncMock(return_value=mock_repositories['mqtt_service'])
        ):
            # Act
            response = client.post("/api/v1/access/validate", json={
                "card_id": "TEST123",
                "door_id": self.TEST_DOOR_ID
            })
        
        # Assert
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"]
    
    @patch('app.api.v1.access.ValidateAccessUseCase')
    def test_validate_access_denied(self, mock_use_case_class, client, mock_repositories):
        """Test access validation when access is denied."""
        # Arrange
        mock_use_case = AsyncMock()
        mock_use_case_class.return_value = mock_use_case
        mock_use_case.execute.side_effect = AccessDeniedError("Access denied: No permission")
        
        # Mock all dependencies
        with patch.multiple(
            'app.api.v1.access',
            get_card_repository=AsyncMock(return_value=mock_repositories['card_repository']),
            get_door_repository=AsyncMock(return_value=mock_repositories['door_repository']),
            get_permission_repository=AsyncMock(return_value=mock_repositories['permission_repository']),
            get_user_repository=AsyncMock(return_value=mock_repositories['user_repository']),
            get_mqtt_service=AsyncMock(return_value=mock_repositories['mqtt_service'])
        ):
            # Act
            response = client.post("/api/v1/access/validate", json={
                "card_id": "TEST123",
                "door_id": self.TEST_DOOR_ID
            })
        
        # Assert
        assert response.status_code == 403
        assert "No permission" in response.json()["detail"]
    
    @patch('app.api.v1.access.ValidateAccessUseCase')
    def test_validate_access_internal_error(self, mock_use_case_class, client, mock_repositories):
        """Test access validation with internal server error."""
        # Arrange
        mock_use_case = AsyncMock()
        mock_use_case_class.return_value = mock_use_case
        mock_use_case.execute.side_effect = Exception("Database connection error")
        
        # Mock all dependencies
        with patch.multiple(
            'app.api.v1.access',
            get_card_repository=AsyncMock(return_value=mock_repositories['card_repository']),
            get_door_repository=AsyncMock(return_value=mock_repositories['door_repository']),
            get_permission_repository=AsyncMock(return_value=mock_repositories['permission_repository']),
            get_user_repository=AsyncMock(return_value=mock_repositories['user_repository']),
            get_mqtt_service=AsyncMock(return_value=mock_repositories['mqtt_service'])
        ):
            # Act
            response = client.post("/api/v1/access/validate", json={
                "card_id": "TEST123",
                "door_id": self.TEST_DOOR_ID
            })
        
        # Assert
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
    
    def test_access_endpoint_content_type(self, client):
        """Test that endpoint requires proper content type."""
        response = client.post("/api/v1/access/validate", data="invalid")
        assert response.status_code in [422, 400]  # Should reject non-JSON
    
    def test_access_endpoint_documentation(self):
        """Test that endpoint has proper OpenAPI documentation."""
        from app.api.v1.access import router
        
        # Find the validate_access route
        validate_route = None
        for route in router.routes:
            if hasattr(route, 'path') and route.path == '/validate':
                validate_route = route
                break
        
        assert validate_route is not None
        assert validate_route.methods == {'POST'}
        
        # Check that the endpoint function has proper documentation
        from app.api.v1.access import validate_access
        assert validate_access.__doc__ is not None
        assert "Validate access request from IoT device" in validate_access.__doc__