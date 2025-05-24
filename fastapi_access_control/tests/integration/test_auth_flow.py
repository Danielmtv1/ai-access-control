import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.domain.entities.user import User, Role, UserStatus
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims
from datetime import datetime, UTC

class TestAuthenticationFlow:
    """Integration tests for complete authentication flow"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    def test_complete_auth_flow_mock(self, client):
        """Test complete authentication flow with mocked dependencies"""
        
        # Mock the dependencies
        with patch('app.interfaces.api.dependencies.auth_dependencies.get_user_repository') as mock_repo_dep, \
             patch('app.interfaces.api.dependencies.auth_dependencies.get_auth_service') as mock_auth_dep:
            
            # Setup mocks
            mock_repo = AsyncMock()
            mock_auth = AuthService()
            mock_repo_dep.return_value = mock_repo
            mock_auth_dep.return_value = mock_auth
            
            # Create test user
            test_password = "TestPassword123!"
            hashed_password = mock_auth.hash_password(test_password)
            
            test_user = User(
                id=1,
                email="test@example.com",
                hashed_password=hashed_password,
                full_name="Test User",
                roles=[Role.USER],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(UTC)
            )
            
            # Configure mock repository
            mock_repo.get_by_email.return_value = test_user
            mock_repo.update.return_value = test_user
            
            # Test login
            login_response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": test_password
            })
            
            assert login_response.status_code == 200
            login_data = login_response.json()
            
            # Verify login response structure
            assert "access_token" in login_data
            assert "refresh_token" in login_data
            assert "token_type" in login_data
            assert "expires_in" in login_data
            assert "user" in login_data
            
            # Extract token for authenticated requests
            access_token = login_data["access_token"]
            
            # Test authenticated endpoint
            me_response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            assert me_response.status_code == 200
            me_data = me_response.json()
            
            assert me_data["user"]["email"] == "test@example.com"
            assert me_data["user"]["full_name"] == "Test User"
    
    def test_login_validation_errors(self, client):
        """Test login validation error responses"""
        
        # Test missing fields
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422
        
        # Test invalid email format
        response = client.post("/api/v1/auth/login", json={
            "email": "not-an-email",
            "password": "somepassword"
        })
        assert response.status_code == 422
        
        # Test password too short
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "123"
        })
        assert response.status_code == 422
    
    def test_unauthorized_access(self, client):
        """Test accessing protected endpoints without token"""
        
        # Test /me endpoint without token
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 422  # No Authorization header
        
        # Test with invalid token
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    def test_token_refresh_flow(self, client):
        """Test token refresh functionality"""
        
        with patch('app.interfaces.api.dependencies.auth_dependencies.get_user_repository') as mock_repo_dep, \
             patch('app.interfaces.api.dependencies.auth_dependencies.get_auth_service') as mock_auth_dep:
            
            mock_repo = AsyncMock()
            mock_auth = AuthService()
            mock_repo_dep.return_value = mock_repo
            mock_auth_dep.return_value = mock_auth
            
            # Create test user
            test_user = User(
                id=1,
                email="test@example.com",
                hashed_password="hashed",
                full_name="Test User",
                roles=[Role.USER],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(UTC)
            )
            
            mock_repo.get_by_id.return_value = test_user
            
            # Generate a refresh token
            token_pair = mock_auth.generate_token_pair(test_user)
            
            # Test refresh endpoint
            refresh_response = client.post("/api/v1/auth/refresh", json={
                "refresh_token": token_pair.refresh_token
            })
            
            assert refresh_response.status_code == 200
            refresh_data = refresh_response.json()
            
            # Verify new tokens are provided
            assert "access_token" in refresh_data
            assert "refresh_token" in refresh_data
            assert refresh_data["access_token"] != token_pair.access_token  # Should be new

class TestRoleBasedAccess:
    """Tests for role-based access control"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_role_based_access_patterns(self):
        """Test role-based access control patterns"""
        
        # Test admin user
        admin_claims = UserClaims(
            user_id=1,
            email="admin@example.com",
            full_name="Admin User",
            roles=["admin", "operator"]
        )
        
        assert admin_claims.has_role("admin")
        assert admin_claims.has_any_role(["admin"])
        assert admin_claims.has_any_role(["admin", "operator"])
        
        # Test regular user
        user_claims = UserClaims(
            user_id=2,
            email="user@example.com",
            full_name="Regular User",
            roles=["user"]
        )
        
        assert not user_claims.has_role("admin")
        assert user_claims.has_role("user")
        assert not user_claims.has_any_role(["admin", "operator"]) 