import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, UTC, timedelta
from uuid import uuid4
from app.domain.entities.permission import Permission
from app.domain.entities.user import User, Role, UserStatus
from app.domain.entities.door import Door, DoorStatus
from app.domain.entities.card import Card, CardType, CardStatus
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_DOOR_UUID, SAMPLE_CARD_UUID, SAMPLE_ADMIN_UUID

class TestPermissionsAPI:
    """Integration tests for Permissions API endpoints"""
    
    @pytest.fixture
    def client(self):
        """
        Provides an HTTP client for testing FastAPI endpoints.
        
        Returns:
            TestClient: An instance of TestClient configured with the FastAPI app.
        """
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def mock_admin_user(self):
        """
        Creates and returns a mock admin user entity for testing purposes.
        
        Returns:
            User: A user instance with admin role, active status, and sample data.
        """
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
    
    @pytest.fixture
    def mock_regular_user(self):
        """
        Creates and returns a mock regular user entity for testing purposes.
        
        Returns:
            User: A user instance with the USER role and active status.
        """
        return User(
            id=SAMPLE_USER_UUID,
            email="user@test.com",
            hashed_password="hashed_password",
            full_name="Regular User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
    
    @pytest.fixture
    def mock_permission(self):
        """
        Creates and returns a mock Permission object with preset test data.
        
        Returns:
            Permission: A Permission instance with sample user, door, and card IDs, active status, and valid date range.
        """
        return Permission(
            id=uuid4(),
            user_id=SAMPLE_USER_UUID,
            door_id=SAMPLE_DOOR_UUID,
            card_id=SAMPLE_CARD_UUID,
            status="active",
            valid_from=datetime.now(UTC),
            valid_until=datetime.now(UTC) + timedelta(days=30),
            access_schedule=None,
            pin_required=False,
            created_by=SAMPLE_ADMIN_UUID,
            last_used=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
    
    def setup_auth_override(self, client, user):
        """
        Overrides the authentication dependency to simulate a logged-in user for testing.
        
        Args:
            client: The FastAPI test client instance.
            user: The user entity to be returned by the authentication dependency.
        """
        from app.api.dependencies.auth_dependencies import get_current_active_user
        client.app.dependency_overrides[get_current_active_user] = lambda: user
        
    def cleanup_overrides(self, client):
        """
        Removes all dependency overrides from the FastAPI test client.
        
        This helper ensures that any custom dependency overrides set during a test are cleared, restoring the application's dependency injection to its default state.
        """
        client.app.dependency_overrides.clear()

    def test_create_permission_success(self, client, mock_admin_user, mock_permission):
        """
        Tests that an admin user can successfully create a permission via the API.
        
        Simulates authentication as an admin, mocks the permission creation use case to return a mock permission, sends a POST request with valid permission data, and asserts that the response status is 201 and the returned data matches the input.
        """
        with patch('app.api.v1.permissions.CreatePermissionUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = mock_permission
            
            # Test data
            permission_data = {
                "user_id": str(SAMPLE_USER_UUID),
                "door_id": str(SAMPLE_DOOR_UUID),
                "card_id": str(SAMPLE_CARD_UUID),
                "valid_from": "2024-01-01T00:00:00",
                "valid_until": "2024-12-31T23:59:59",
                "pin_required": False
            }
            
            # Make request
            response = client.post("/api/v1/permissions/", json=permission_data)
            
            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert data["user_id"] == str(SAMPLE_USER_UUID)
            assert data["door_id"] == str(SAMPLE_DOOR_UUID)
            assert data["card_id"] == str(SAMPLE_CARD_UUID)
            assert data["status"] == "active"
            assert data["pin_required"] == False
            
            # Verify use case was called
            mock_use_case.execute.assert_called_once()
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_create_permission_unauthorized(self, client):
        """
        Tests that creating a permission without authentication returns a 401 Unauthorized response.
        """
        permission_data = {
            "user_id": str(SAMPLE_USER_UUID),
            "door_id": str(SAMPLE_DOOR_UUID),
            "card_id": str(SAMPLE_CARD_UUID),
            "pin_required": False
        }
        
        response = client.post("/api/v1/permissions/", json=permission_data)
        assert response.status_code == 401

    def test_list_permissions_success(self, client, mock_admin_user, mock_permission):
        """
        Tests that an admin user can successfully retrieve a paginated list of permissions.
        
        Verifies that the permissions listing endpoint returns the correct pagination metadata and permission data when accessed by an authenticated admin user.
        """
        with patch('app.api.v1.permissions.ListPermissionsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = {
                "permissions": [mock_permission],
                "total": 1,
                "page": 1,
                "size": 50,
                "pages": 1
            }
            
            # Make request
            response = client.get("/api/v1/permissions/")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["page"] == 1
            assert data["size"] == 50
            assert data["pages"] == 1
            assert len(data["permissions"]) == 1
            assert data["permissions"][0]["user_id"] == str(SAMPLE_USER_UUID)
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_list_permissions_with_filters(self, client, mock_admin_user, mock_permission):
        """
        Tests listing permissions with query filters as an admin user.
        
        Sends a GET request to the permissions endpoint with filter parameters, mocks the use case to return filtered results, asserts the response contains the expected filtered permissions, and verifies the use case is called with correct filter arguments.
        """
        with patch('app.api.v1.permissions.ListPermissionsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = {
                "permissions": [mock_permission],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1
            }
            
            # Make request with filters
            response = client.get(
                "/api/v1/permissions/",
                params={
                    "user_id": str(SAMPLE_USER_UUID),
                    "status": "active",
                    "page": 1,
                    "size": 10
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["permissions"]) == 1
            
            # Verify use case was called with filters
            mock_use_case.execute.assert_called_once_with(
                user_id=SAMPLE_USER_UUID,
                door_id=None,
                card_id=None,
                status="active",
                created_by=None,
                valid_only=None,
                expired_only=None,
                page=1,
                size=10
            )
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_permission_by_id_success(self, client, mock_admin_user, mock_permission):
        """
        Tests that an admin user can successfully retrieve a permission by its ID.
        
        Verifies that the API returns a 200 status and the correct permission data when the permission exists.
        """
        with patch('app.api.v1.permissions.GetPermissionUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = mock_permission
            
            # Make request
            permission_id = str(mock_permission.id)
            response = client.get(f"/api/v1/permissions/{permission_id}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == permission_id
            assert data["user_id"] == str(SAMPLE_USER_UUID)
            assert data["door_id"] == str(SAMPLE_DOOR_UUID)
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_permission_not_found(self, client, mock_admin_user):
        """
        Tests that retrieving a permission with a non-existent ID returns a 404 Not Found response.
        """
        with patch('app.api.v1.permissions.GetPermissionUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case to raise exception
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            from app.domain.exceptions import PermissionNotFoundError
            mock_use_case.execute.side_effect = PermissionNotFoundError("permission-id")
            
            # Make request
            response = client.get(f"/api/v1/permissions/{uuid4()}")
            
            # Assertions
            assert response.status_code == 404
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_update_permission_success(self, client, mock_admin_user, mock_permission):
        """
        Tests that an admin user can successfully update a permission via the API.
        
        Simulates authentication as an admin, mocks the update use case to return an updated permission, sends a PUT request with update data, and verifies the response reflects the updated fields.
        """
        with patch('app.api.v1.permissions.UpdatePermissionUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            updated_permission = mock_permission
            updated_permission.pin_required = True
            mock_use_case.execute.return_value = updated_permission
            
            # Test data
            update_data = {
                "pin_required": True,
                "status": "active"
            }
            
            # Make request
            permission_id = str(mock_permission.id)
            response = client.put(f"/api/v1/permissions/{permission_id}", json=update_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["pin_required"] == True
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_delete_permission_success(self, client, mock_admin_user, mock_permission):
        """
        Tests that an admin user can successfully delete a permission via the API.
        
        Verifies that the DELETE endpoint returns a 204 No Content status when the permission is deleted, and that authentication and use case execution are handled correctly.
        """
        with patch('app.api.v1.permissions.DeletePermissionUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = True
            
            # Make request
            permission_id = str(mock_permission.id)
            response = client.delete(f"/api/v1/permissions/{permission_id}")
            
            # Assertions
            assert response.status_code == 204
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_revoke_permission_success(self, client, mock_admin_user, mock_permission):
        """
        Tests that an admin user can successfully revoke a permission, updating its status to "suspended".
        """
        with patch('app.api.v1.permissions.RevokePermissionUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            revoked_permission = mock_permission
            revoked_permission.status = "suspended"
            mock_use_case.execute.return_value = revoked_permission
            
            # Make request
            permission_id = str(mock_permission.id)
            response = client.post(f"/api/v1/permissions/{permission_id}/revoke")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "suspended"
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_user_permissions_success(self, client, mock_admin_user, mock_permission):
        """
        Tests retrieving all permissions for a specific user as an admin.
        
        Verifies that the endpoint returns a list of permissions associated with the given user ID and responds with HTTP 200 on success.
        """
        with patch('app.api.v1.permissions.GetUserPermissionsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = [mock_permission]
            
            # Make request
            response = client.get(f"/api/v1/permissions/users/{SAMPLE_USER_UUID}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["user_id"] == str(SAMPLE_USER_UUID)
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_door_permissions_success(self, client, mock_admin_user, mock_permission):
        """
        Tests retrieving all permissions associated with a specific door as an admin user.
        
        Verifies that the API returns a list of permissions for the given door ID with a 200 status code when accessed by an authenticated admin.
        """
        with patch('app.api.v1.permissions.GetDoorPermissionsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = [mock_permission]
            
            # Make request
            response = client.get(f"/api/v1/permissions/doors/{SAMPLE_DOOR_UUID}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["door_id"] == str(SAMPLE_DOOR_UUID)
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_bulk_create_permissions_success(self, client, mock_admin_user, mock_permission):
        """
        Tests successful bulk creation of permissions via the API.
        
        Simulates an authenticated admin user making a POST request to the bulk permissions endpoint, mocks the use case to return a successful creation summary, and verifies the response contains the correct counts and created permissions.
        """
        with patch('app.api.v1.permissions.BulkCreatePermissionsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = {
                "created": [mock_permission],
                "failed": [],
                "total_requested": 1,
                "total_created": 1,
                "total_failed": 0
            }
            
            # Test data
            bulk_data = {
                "permissions": [
                    {
                        "user_id": str(SAMPLE_USER_UUID),
                        "door_id": str(SAMPLE_DOOR_UUID),
                        "card_id": str(SAMPLE_CARD_UUID),
                        "pin_required": False
                    }
                ]
            }
            
            # Make request
            response = client.post("/api/v1/permissions/bulk", json=bulk_data)
            
            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert data["total_requested"] == 1
            assert data["total_created"] == 1
            assert data["total_failed"] == 0
            assert len(data["created"]) == 1
            assert len(data["failed"]) == 0
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_permission_validation_errors(self, client, mock_admin_user):
        """
        Tests that creating a permission with missing or invalid fields returns validation errors.
        
        Verifies that the API responds with HTTP 422 when required fields are missing or UUIDs are invalid during permission creation.
        """
        # Setup authentication
        self.setup_auth_override(client, mock_admin_user)
        
        # Test missing required fields
        invalid_data = {
            "door_id": str(SAMPLE_DOOR_UUID),
            # Missing user_id
        }
        
        response = client.post("/api/v1/permissions/", json=invalid_data)
        assert response.status_code == 422
        
        # Test invalid UUID format
        invalid_data = {
            "user_id": "invalid-uuid",
            "door_id": str(SAMPLE_DOOR_UUID)
        }
        
        response = client.post("/api/v1/permissions/", json=invalid_data)
        assert response.status_code == 422
        
        # Cleanup
        self.cleanup_overrides(client)