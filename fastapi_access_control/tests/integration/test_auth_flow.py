import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.domain.entities.user import User, Role, UserStatus
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_CARD_UUID_2, SAMPLE_DOOR_UUID, SAMPLE_DOOR_UUID_2
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims
from datetime import datetime, timezone, UTC

class TestAuthenticationFlow:
    """Integration tests for complete authentication flow"""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)
    
    def test_complete_auth_flow_mock(self, client):
        """
        Tests the complete authentication flow using mocked user repository and authentication service.
        
        Simulates a login request with valid credentials, verifies the response contains valid JWT access and refresh tokens, and checks the structure of the authentication response. Dependency overrides are used to inject mocks, and are cleared after the test.
        """
        
        # Create mocks
        mock_repo = AsyncMock()
        mock_auth = AuthService()
        
        # Use FastAPI dependency override system
        from app.api.v1.auth import get_user_repository, get_auth_service
        client.app.dependency_overrides[get_user_repository] = lambda: mock_repo
        client.app.dependency_overrides[get_auth_service] = lambda: mock_auth
        
        try:
            
            # Create test user
            test_password = "TestPassword123!"
            hashed_password = mock_auth.hash_password(test_password)
            
            test_user = User(
                id=SAMPLE_USER_UUID,
                email="test@example.com",
                hashed_password=hashed_password,
                full_name="Test User",
                roles=[Role.USER],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
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
            
            # Verify tokens are valid JWT format (basic validation)
            access_token = login_data["access_token"]
            assert len(access_token.split('.')) == 3  # JWT has 3 parts separated by dots
            
            refresh_token = login_data["refresh_token"]
            assert len(refresh_token.split('.')) == 3  # JWT has 3 parts separated by dots
            
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()
    
    def test_login_validation_errors(self, client):
        """
        Verifies that the login endpoint returns validation errors for missing or invalid input.
        
        Sends POST requests to the login endpoint with missing fields, invalid email format, and too short password, asserting that each returns a 422 Unprocessable Entity status.
        """
        
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
        """
        Tests that access to protected endpoints is denied without a valid authentication token.
        
        Sends requests to a protected endpoint both without an authentication token and with an invalid token, asserting that both cases result in a 401 Unauthorized response.
        """
        
        # Test doors endpoint without token (it requires authentication)
        response = client.get("/api/v1/doors/")
        assert response.status_code == 401  # Unauthorized
        
        # Test with invalid token
        response = client.get(
            "/api/v1/doors/",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    def test_token_refresh_flow(self, client):
        """
        Tests the token refresh endpoint to ensure a valid refresh token issues new access and refresh tokens.
        
        Creates a mock user repository and authentication service, injects them via FastAPI dependency overrides, and verifies that posting a valid refresh token returns a new access token and refresh token. Cleans up dependency overrides after the test.
        """
        
        # Create mocks
        mock_repo = AsyncMock()
        mock_auth = AuthService()
        
        # Use FastAPI dependency override system
        from app.api.v1.auth import get_user_repository, get_auth_service
        client.app.dependency_overrides[get_user_repository] = lambda: mock_repo
        client.app.dependency_overrides[get_auth_service] = lambda: mock_auth
        
        try:
            # Create test user
            test_user = User(
                id=SAMPLE_USER_UUID,
                email="test@example.com",
                hashed_password="hashed",
                full_name="Test User",
                roles=[Role.USER],
                status=UserStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            # Set up async mock to return test user
            mock_repo.get_by_id = AsyncMock(return_value=test_user)
            
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
            
        finally:
            # Clean up dependency overrides
            client.app.dependency_overrides.clear()

class TestRoleBasedAccess:
    """Tests for role-based access control"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_role_based_access_patterns(self):
        """
        Verifies that role-based access control methods on UserClaims correctly identify user roles.
        
        Tests that users with different roles are accurately recognized by has_role and has_any_role methods, ensuring proper distinction between admin and regular users.
        """
        
        # Test admin user
        admin_claims = UserClaims(
            user_id=SAMPLE_USER_UUID,
            email="admin@example.com",
            full_name="Admin User",
            roles=["admin", "operator"]
        )
        
        assert admin_claims.has_role("admin")
        assert admin_claims.has_any_role(["admin"])
        assert admin_claims.has_any_role(["admin", "operator"])
        
        # Test regular user
        user_claims = UserClaims(
            user_id=SAMPLE_USER_UUID,
            email="user@example.com",
            full_name="Regular User",
            roles=["user"]
        )
        
        assert not user_claims.has_role("admin")
        assert user_claims.has_role("user")
        assert not user_claims.has_any_role(["admin", "operator"]) 