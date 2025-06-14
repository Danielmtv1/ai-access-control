import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, UTC
from uuid import uuid4
from app.domain.entities.user import User, Role, UserStatus
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_ADMIN_UUID

class TestUsersAPI:
    """Integration tests for Users API endpoints"""
    
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
    def mock_operator_user(self):
        """Mock operator user for testing."""
        return User(
            id=uuid4(),
            email="operator@test.com",
            hashed_password="hashed_password",
            full_name="Operator User",
            roles=[Role.OPERATOR],
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

    def test_create_user_success_admin(self, client, mock_admin_user):
        """Test successful user creation by admin"""
        with patch('app.api.v1.users.CreateUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            new_user = User(
                id=uuid4(),
                email="newuser@test.com",
                hashed_password="hashed_password",
                full_name="New User",
                roles=[Role.USER],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            mock_use_case.execute.return_value = new_user
            
            # Test data
            user_data = {
                "email": "newuser@test.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
                "roles": ["user"],
                "status": "active"
            }
            
            # Make request
            response = client.post("/api/v1/users/", json=user_data)
            
            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert data["email"] == "newuser@test.com"
            assert data["full_name"] == "New User"
            assert data["roles"] == ["user"]
            assert data["status"] == "active"
            
            # Verify use case was called
            mock_use_case.execute.assert_called_once()
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_create_user_forbidden_regular_user(self, client, mock_regular_user):
        """Test user creation forbidden for regular users"""
        # Setup authentication with regular user
        self.setup_auth_override(client, mock_regular_user)
        
        user_data = {
            "email": "newuser@test.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "roles": ["user"]
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 403
        
        # Cleanup
        self.cleanup_overrides(client)

    def test_create_user_unauthorized(self, client):
        """Test user creation without authentication"""
        user_data = {
            "email": "newuser@test.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "roles": ["user"]
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 401

    def test_list_users_success(self, client, mock_admin_user, mock_regular_user):
        """Test successful user listing"""
        with patch('app.api.v1.users.ListUsersUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = {
                "users": [mock_regular_user],
                "total": 1,
                "page": 1,
                "size": 50,
                "pages": 1
            }
            
            # Make request
            response = client.get("/api/v1/users/")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["page"] == 1
            assert data["size"] == 50
            assert data["pages"] == 1
            assert len(data["users"]) == 1
            assert data["users"][0]["email"] == "user@test.com"
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_list_users_with_filters(self, client, mock_admin_user, mock_regular_user):
        """Test user listing with filters"""
        with patch('app.api.v1.users.ListUsersUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = {
                "users": [mock_regular_user],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1
            }
            
            # Make request with filters
            response = client.get(
                "/api/v1/users/",
                params={
                    "status": "active",
                    "role": "user",
                    "search": "user",
                    "page": 1,
                    "size": 10
                }
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["users"]) == 1
            
            # Verify use case was called with filters
            mock_use_case.execute.assert_called_once_with(
                status="active",
                role="user",
                search="user",
                page=1,
                size=10
            )
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_user_stats_success_admin(self, client, mock_admin_user):
        """Test successful user statistics retrieval by admin"""
        with patch('app.api.v1.users.GetUserStatsUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = {
                "total_users": 10,
                "active_users": 8,
                "inactive_users": 1,
                "suspended_users": 1,
                "users_by_role": {
                    "admin": 2,
                    "operator": 3,
                    "user": 4,
                    "viewer": 1
                }
            }
            
            # Make request
            response = client.get("/api/v1/users/stats")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["total_users"] == 10
            assert data["active_users"] == 8
            assert data["inactive_users"] == 1
            assert data["suspended_users"] == 1
            assert data["users_by_role"]["admin"] == 2
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_user_stats_forbidden_regular_user(self, client, mock_regular_user):
        """Test user stats forbidden for regular users"""
        # Setup authentication with regular user
        self.setup_auth_override(client, mock_regular_user)
        
        response = client.get("/api/v1/users/stats")
        assert response.status_code == 403
        
        # Cleanup
        self.cleanup_overrides(client)

    def test_get_user_by_id_success_admin(self, client, mock_admin_user, mock_regular_user):
        """Test successful user retrieval by ID (admin)"""
        with patch('app.api.v1.users.GetUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = mock_regular_user
            
            # Make request
            response = client.get(f"/api/v1/users/{SAMPLE_USER_UUID}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(SAMPLE_USER_UUID)
            assert data["email"] == "user@test.com"
            assert data["full_name"] == "Regular User"
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_user_by_id_own_profile(self, client, mock_regular_user):
        """Test user can view their own profile"""
        with patch('app.api.v1.users.GetUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_regular_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = mock_regular_user
            
            # Make request for own profile
            response = client.get(f"/api/v1/users/{SAMPLE_USER_UUID}")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(SAMPLE_USER_UUID)
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_get_user_by_id_forbidden_other_profile(self, client, mock_regular_user):
        """Test user cannot view other user's profile"""
        # Setup authentication with regular user
        self.setup_auth_override(client, mock_regular_user)
        
        # Try to access different user's profile
        other_user_id = uuid4()
        response = client.get(f"/api/v1/users/{other_user_id}")
        assert response.status_code == 403
        
        # Cleanup
        self.cleanup_overrides(client)

    def test_get_user_by_email_success(self, client, mock_admin_user, mock_regular_user):
        """Test successful user retrieval by email"""
        with patch('app.api.v1.users.GetUserByEmailUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = mock_regular_user
            
            # Make request
            response = client.get("/api/v1/users/email/user@test.com")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "user@test.com"
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_update_user_success_admin(self, client, mock_admin_user, mock_regular_user):
        """Test successful user update by admin"""
        with patch('app.api.v1.users.UpdateUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            updated_user = mock_regular_user
            updated_user.full_name = "Updated User"
            updated_user.roles = [Role.OPERATOR]
            mock_use_case.execute.return_value = updated_user
            
            # Test data
            update_data = {
                "full_name": "Updated User",
                "roles": ["operator"],
                "status": "active"
            }
            
            # Make request
            response = client.put(f"/api/v1/users/{SAMPLE_USER_UUID}", json=update_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated User"
            assert data["roles"] == ["operator"]
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_update_user_own_profile_limited(self, client, mock_regular_user):
        """Test user can update own profile but limited fields"""
        with patch('app.api.v1.users.UpdateUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_regular_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            updated_user = mock_regular_user
            updated_user.full_name = "Updated Name"
            mock_use_case.execute.return_value = updated_user
            
            # Test data (only full_name allowed for regular users)
            update_data = {
                "full_name": "Updated Name"
            }
            
            # Make request
            response = client.put(f"/api/v1/users/{SAMPLE_USER_UUID}", json=update_data)
            
            # Assertions
            assert response.status_code == 200
            
            # Test forbidden fields for regular users
            forbidden_data = {
                "full_name": "Updated Name",
                "roles": ["admin"],  # Not allowed
                "status": "suspended"  # Not allowed
            }
            
            response = client.put(f"/api/v1/users/{SAMPLE_USER_UUID}", json=forbidden_data)
            assert response.status_code == 403
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_delete_user_success_admin(self, client, mock_admin_user):
        """Test successful user deletion by admin"""
        with patch('app.api.v1.users.DeleteUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = True
            
            # Make request
            response = client.delete(f"/api/v1/users/{SAMPLE_USER_UUID}")
            
            # Assertions
            assert response.status_code == 204
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_delete_user_forbidden_self_deletion(self, client, mock_admin_user):
        """Test admin cannot delete their own account"""
        # Setup authentication
        self.setup_auth_override(client, mock_admin_user)
        
        # Try to delete own account
        response = client.delete(f"/api/v1/users/{SAMPLE_ADMIN_UUID}")
        assert response.status_code == 400
        
        # Cleanup
        self.cleanup_overrides(client)

    def test_delete_user_forbidden_regular_user(self, client, mock_regular_user):
        """Test user deletion forbidden for regular users"""
        # Setup authentication with regular user
        self.setup_auth_override(client, mock_regular_user)
        
        response = client.delete(f"/api/v1/users/{SAMPLE_USER_UUID}")
        assert response.status_code == 403
        
        # Cleanup
        self.cleanup_overrides(client)

    def test_suspend_user_success_admin(self, client, mock_admin_user, mock_regular_user):
        """Test successful user suspension by admin"""
        with patch('app.api.v1.users.SuspendUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            suspended_user = mock_regular_user
            suspended_user.status = UserStatus.SUSPENDED
            mock_use_case.execute.return_value = suspended_user
            
            # Make request
            response = client.post(f"/api/v1/users/{SAMPLE_USER_UUID}/suspend")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "suspended"
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_suspend_user_forbidden_self_suspension(self, client, mock_admin_user):
        """Test admin cannot suspend their own account"""
        # Setup authentication
        self.setup_auth_override(client, mock_admin_user)
        
        # Try to suspend own account
        response = client.post(f"/api/v1/users/{SAMPLE_ADMIN_UUID}/suspend")
        assert response.status_code == 400
        
        # Cleanup
        self.cleanup_overrides(client)

    def test_activate_user_success_admin(self, client, mock_admin_user, mock_regular_user):
        """Test successful user activation by admin"""
        with patch('app.api.v1.users.ActivateUserUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            activated_user = mock_regular_user
            activated_user.status = UserStatus.ACTIVE
            mock_use_case.execute.return_value = activated_user
            
            # Make request
            response = client.post(f"/api/v1/users/{SAMPLE_USER_UUID}/activate")
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_change_password_success_own_account(self, client, mock_regular_user):
        """Test successful password change for own account"""
        with patch('app.api.v1.users.ChangePasswordUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_regular_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = mock_regular_user
            
            # Test data
            password_data = {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!"
            }
            
            # Make request
            response = client.post(f"/api/v1/users/{SAMPLE_USER_UUID}/change-password", json=password_data)
            
            # Assertions
            assert response.status_code == 200
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_change_password_admin_for_other_user(self, client, mock_admin_user, mock_regular_user):
        """Test admin can change password for other users"""
        with patch('app.api.v1.users.ChangePasswordUseCase') as mock_use_case_class:
            
            # Setup authentication
            self.setup_auth_override(client, mock_admin_user)
            
            # Mock the use case
            mock_use_case = AsyncMock()
            mock_use_case_class.return_value = mock_use_case
            mock_use_case.execute.return_value = mock_regular_user
            
            # Test data
            password_data = {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!"
            }
            
            # Make request
            response = client.post(f"/api/v1/users/{SAMPLE_USER_UUID}/change-password", json=password_data)
            
            # Assertions
            assert response.status_code == 200
            
            # Cleanup
            self.cleanup_overrides(client)

    def test_change_password_forbidden_other_user(self, client, mock_regular_user):
        """Test regular user cannot change password for other users"""
        # Setup authentication with regular user
        self.setup_auth_override(client, mock_regular_user)
        
        # Try to change password for different user
        other_user_id = uuid4()
        password_data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!"
        }
        
        response = client.post(f"/api/v1/users/{other_user_id}/change-password", json=password_data)
        assert response.status_code == 403
        
        # Cleanup
        self.cleanup_overrides(client)

    def test_user_validation_errors(self, client, mock_admin_user):
        """Test user creation with validation errors"""
        # Setup authentication
        self.setup_auth_override(client, mock_admin_user)
        
        # Test missing required fields
        invalid_data = {
            "full_name": "Test User",
            # Missing email and password
        }
        
        response = client.post("/api/v1/users/", json=invalid_data)
        assert response.status_code == 422
        
        # Test invalid email format
        invalid_data = {
            "email": "invalid-email",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/users/", json=invalid_data)
        assert response.status_code == 422
        
        # Test weak password
        invalid_data = {
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/users/", json=invalid_data)
        assert response.status_code == 422
        
        # Cleanup
        self.cleanup_overrides(client)