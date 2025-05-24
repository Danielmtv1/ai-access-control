import pytest
import asyncio
from datetime import datetime, UTC
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.domain.entities.user import User, Role, UserStatus
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims, TokenPair
from app.application.use_cases.auth_use_cases import (
    AuthenticateUserUseCase, RefreshTokenUseCase, CreateUserUseCase, 
    AuthenticationError
)

class TestAuthService:
    """Tests for AuthService domain service"""
    
    def test_hash_password(self):
        """Test password hashing"""
        auth_service = AuthService()
        password = "TestPassword123!"
        
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert auth_service.verify_password(password, hashed)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        auth_service = AuthService()
        password = "TestPassword123!"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        auth_service = AuthService()
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_generate_access_token(self):
        """Test JWT access token generation"""
        auth_service = AuthService()
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        token = auth_service.generate_access_token(user)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = auth_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
    
    def test_generate_token_pair(self):
        """Test token pair generation"""
        auth_service = AuthService()
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        token_pair = auth_service.generate_token_pair(user)
        
        assert isinstance(token_pair, TokenPair)
        assert token_pair.access_token
        assert token_pair.refresh_token
        assert token_pair.token_type == "bearer"
        assert token_pair.expires_in > 0
    
    def test_extract_user_claims(self):
        """Test extracting user claims from token"""
        auth_service = AuthService()
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER, Role.VIEWER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        token = auth_service.generate_access_token(user)
        claims = auth_service.extract_user_claims(token)
        
        assert isinstance(claims, UserClaims)
        assert claims.user_id == 1
        assert claims.email == "test@example.com"
        assert claims.full_name == "Test User"
        assert "user" in claims.roles
        assert "viewer" in claims.roles

class TestAuthUseCases:
    """Tests for authentication use cases"""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # Mock repository
        mock_repo = AsyncMock()
        auth_service = AuthService()
        
        # Create test user
        password = "TestPassword123!"
        hashed_password = auth_service.hash_password(password)
        
        user = User(
            id=1,
            email="test@example.com",
            hashed_password=hashed_password,
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        mock_repo.get_by_email.return_value = user
        mock_repo.update.return_value = user
        
        # Execute use case
        use_case = AuthenticateUserUseCase(mock_repo, auth_service)
        result = await use_case.execute("test@example.com", password)
        
        # Verify result
        assert isinstance(result, TokenPair)
        assert result.access_token
        assert result.refresh_token
        
        # Verify repository calls
        mock_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_email(self):
        """Test authentication with invalid email"""
        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None
        
        auth_service = AuthService()
        use_case = AuthenticateUserUseCase(mock_repo, auth_service)
        
        with pytest.raises(AuthenticationError) as exc_info:
            await use_case.execute("nonexistent@example.com", "password")
        
        assert "Invalid email or password" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password"""
        mock_repo = AsyncMock()
        auth_service = AuthService()
        
        # Create user with different password
        correct_password = "CorrectPassword123!"
        wrong_password = "WrongPassword456!"
        hashed_password = auth_service.hash_password(correct_password)
        
        user = User(
            id=1,
            email="test@example.com",
            hashed_password=hashed_password,
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        mock_repo.get_by_email.return_value = user
        
        use_case = AuthenticateUserUseCase(mock_repo, auth_service)
        
        with pytest.raises(AuthenticationError) as exc_info:
            await use_case.execute("test@example.com", wrong_password)
        
        assert "Invalid email or password" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self):
        """Test authentication with inactive user"""
        mock_repo = AsyncMock()
        auth_service = AuthService()
        
        password = "TestPassword123!"
        hashed_password = auth_service.hash_password(password)
        
        # User is inactive
        user = User(
            id=1,
            email="test@example.com",
            hashed_password=hashed_password,
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.INACTIVE,  # Inactive status
            created_at=datetime.now(UTC)
        )
        
        mock_repo.get_by_email.return_value = user
        
        use_case = AuthenticateUserUseCase(mock_repo, auth_service)
        
        with pytest.raises(AuthenticationError) as exc_info:
            await use_case.execute("test@example.com", password)
        
        assert "User account is not active" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation"""
        mock_repo = AsyncMock()
        auth_service = AuthService()
        
        # Mock no existing user
        mock_repo.get_by_email.return_value = None
        
        # Mock created user
        created_user = User(
            id=1,
            email="new@example.com",
            hashed_password="hashed",
            full_name="New User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        mock_repo.create.return_value = created_user
        
        use_case = CreateUserUseCase(mock_repo, auth_service)
        result = await use_case.execute(
            email="new@example.com",
            password="NewPassword123!",
            full_name="New User"
        )
        
        assert isinstance(result, User)
        assert result.email == "new@example.com"
        assert result.full_name == "New User"
        assert Role.USER in result.roles
        
        mock_repo.create.assert_called_once()

class TestAuthAPI:
    """Integration tests for auth API endpoints"""
    
    def test_auth_endpoints_exist(self):
        """Test that auth endpoints are accessible"""
        client = TestClient(app)
        
        # Test that endpoints return proper responses (even if unauthorized)
        response = client.get("/api/v1/auth/me")
        assert response.status_code in [401, 422]  # Unauthorized or validation error
        
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422  # Validation error
    
    def test_login_validation(self):
        """Test login request validation"""
        client = TestClient(app)
        
        # Test with invalid data
        response = client.post("/api/v1/auth/login", json={
            "email": "not-an-email",
            "password": "123"  # Too short
        })
        
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
    
    def test_openapi_docs(self):
        """Test that OpenAPI docs include auth endpoints"""
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # Check that auth endpoints are documented
        assert "/api/v1/auth/login" in paths
        assert "/api/v1/auth/me" in paths
        assert "/api/v1/auth/refresh" in paths

class TestUserEntity:
    """Tests for User domain entity"""
    
    def test_user_is_active(self):
        """Test user active status check"""
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        assert user.is_active() is True
        
        user.status = UserStatus.INACTIVE
        assert user.is_active() is False
    
    def test_user_has_role(self):
        """Test user role checking"""
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER, Role.VIEWER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        assert user.has_role(Role.USER) is True
        assert user.has_role(Role.VIEWER) is True
        assert user.has_role(Role.ADMIN) is False
    
    def test_user_has_any_role(self):
        """Test user multiple role checking"""
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER, Role.VIEWER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        assert user.has_any_role([Role.USER, Role.ADMIN]) is True
        assert user.has_any_role([Role.ADMIN, Role.OPERATOR]) is False
    
    def test_user_business_logic_permissions(self):
        """Test user business logic for permissions"""
        # Admin user
        admin_user = User(
            id=1,
            email="admin@example.com",
            hashed_password="hashed",
            full_name="Admin User",
            roles=[Role.ADMIN],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        assert admin_user.can_access_admin_panel() is True
        assert admin_user.can_manage_devices() is True
        assert admin_user.can_view_access_logs() is True
        
        # Operator user
        operator_user = User(
            id=2,
            email="operator@example.com",
            hashed_password="hashed",
            full_name="Operator User",
            roles=[Role.OPERATOR],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        assert operator_user.can_access_admin_panel() is False
        assert operator_user.can_manage_devices() is True
        assert operator_user.can_view_access_logs() is True
        
        # Regular user
        regular_user = User(
            id=3,
            email="user@example.com",
            hashed_password="hashed",
            full_name="Regular User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        assert regular_user.can_access_admin_panel() is False
        assert regular_user.can_manage_devices() is False
        assert regular_user.can_view_access_logs() is False
        
        # Viewer user
        viewer_user = User(
            id=4,
            email="viewer@example.com",
            hashed_password="hashed",
            full_name="Viewer User",
            roles=[Role.VIEWER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC)
        )
        
        assert viewer_user.can_access_admin_panel() is False
        assert viewer_user.can_manage_devices() is False
        assert viewer_user.can_view_access_logs() is True

class TestUserClaims:
    """Tests for UserClaims value object"""
    
    def test_user_claims_has_role(self):
        """Test user claims role checking"""
        claims = UserClaims(
            user_id=1,
            email="test@example.com",
            full_name="Test User",
            roles=["user", "viewer"]
        )
        
        assert claims.has_role("user") is True
        assert claims.has_role("viewer") is True
        assert claims.has_role("admin") is False
    
    def test_user_claims_has_any_role(self):
        """Test user claims multiple role checking"""
        claims = UserClaims(
            user_id=1,
            email="test@example.com",
            full_name="Test User",
            roles=["user", "viewer"]
        )
        
        assert claims.has_any_role(["user", "admin"]) is True
        assert claims.has_any_role(["admin", "operator"]) is False
        assert claims.has_any_role([]) is False 