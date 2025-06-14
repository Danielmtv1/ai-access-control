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
    
    @pytest.fixture
    def mock_regular_user(self):
        """Mock regular user for testing."""
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
        """Mock permission for testing."""
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
        """Helper to setup authentication override."""
        from app.api.dependencies.auth_dependencies import get_current_active_user
        client.app.dependency_overrides[get_current_active_user] = lambda: user
        
    def cleanup_overrides(self, client):
        """Helper to cleanup dependency overrides."""
        client.app.dependency_overrides.clear()

    def test_create_permission_success(self, client, mock_admin_user, mock_permission):
        """Test successful permission creation"""
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
        """Test permission creation without authentication"""
        permission_data = {
            "user_id": str(SAMPLE_USER_UUID),
            "door_id": str(SAMPLE_DOOR_UUID),
            "card_id": str(SAMPLE_CARD_UUID),
            "pin_required": False
        }
        
        response = client.post("/api/v1/permissions/", json=permission_data)
        assert response.status_code == 401

    def test_list_permissions_success(self, client, mock_admin_user, mock_permission):
        """Test successful permission listing"""
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
        """Test permission listing with filters"""
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
        """Test successful permission retrieval by ID"""
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
        """Test permission retrieval with non-existent ID"""
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
        """Test successful permission update"""
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
        """Test successful permission deletion"""
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
        """Test successful permission revocation"""
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
        """Test successful user permissions retrieval"""
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
        """Test successful door permissions retrieval"""
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
        """Test successful bulk permission creation"""
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
        """Test permission creation with validation errors"""
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