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
        """
        Provides an HTTP test client for the FastAPI application.
        """
        return TestClient(app)
    
    @pytest.fixture
    def mock_validate_use_case(self):
        """
        Provides an asynchronous mock instance of the ValidateAccessUseCase for testing.
        """
        return AsyncMock()
    
    @pytest.fixture
    def mock_repositories(self):
        """
        Creates and returns a dictionary of async mock objects for repository and service dependencies used in access validation tests.
        
        Returns:
            dict: A mapping of dependency names to their corresponding AsyncMock instances.
        """
        return {
            'card_repository': AsyncMock(),
            'door_repository': AsyncMock(),
            'permission_repository': AsyncMock(),
            'user_repository': AsyncMock(),
            'mqtt_service': AsyncMock()
        }
    
    def test_validate_access_endpoint_exists(self, client):
        """
        Verifies that the access validation endpoint is registered and does not return a 404 status.
        """
        # This should return 422 (validation error) or other error, not 404
        response = client.post("/api/v1/access/validate", json={})
        assert response.status_code != 404
    
    def test_validate_access_request_validation(self, client):
        """
        Tests that the access validation endpoint enforces required fields and correct data types.
        
        Sends POST requests with missing or invalid payloads to verify that the endpoint returns a 422 status code for validation errors.
        """
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
        """
        Tests that the access validation endpoint enforces card_id field constraints.
        
        Sends requests with an empty card_id and a card_id exceeding the maximum length,
        asserting that both cases result in a 422 Unprocessable Entity response.
        """
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
        """
        Verifies that the access validation endpoint enforces PIN length constraints.
        
        Sends requests with PIN values that are too short or too long and asserts that the response status code is 422, indicating validation errors.
        """
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
        """
        Tests that the access validation endpoint returns a successful response with correct data when access is granted.
        
        Simulates a valid access request and verifies that the response includes expected fields such as `access_granted`, `door_name`, `user_name`, `card_type`, and a `timestamp`.
        """
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
        """
        Tests that the access validation endpoint returns a 404 error when the specified card is not found.
        
        Simulates the use case raising an EntityNotFoundError and verifies the response status and error message.
        """
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
        """
        Tests that the access validation endpoint returns a 400 status code and appropriate error message when an invalid (inactive) card is used.
        """
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
        """
        Tests that the access validation endpoint returns a 403 status code and appropriate error message when access is denied due to insufficient permissions.
        """
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
        """
        Tests that the access validation endpoint returns a 500 status code and appropriate error message when an unexpected internal server error occurs during processing.
        """
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
        """
        Tests that the access validation endpoint rejects requests with non-JSON content types.
        
        Sends a POST request with invalid (non-JSON) data and asserts that the response status code indicates a validation or bad request error.
        """
        response = client.post("/api/v1/access/validate", data="invalid")
        assert response.status_code in [422, 400]  # Should reject non-JSON
    
    def test_access_endpoint_documentation(self):
        """
        Verifies that the access validation endpoint is documented in the OpenAPI schema.
        
        Checks that the `/validate` route exists, supports the POST method, and that the endpoint function has a descriptive docstring mentioning "Validate access request from IoT device".
        """
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