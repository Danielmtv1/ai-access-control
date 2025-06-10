"""
Tests for AuthService domain service
"""
import pytest
import jwt
from datetime import datetime, UTC, timedelta
from uuid import UUID, uuid4

from app.domain.entities.user import User, Role, UserStatus
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims, TokenPair


class TestAuthService:
    """Comprehensive tests for AuthService"""
    
    def test_hash_password(self):
        """Test password hashing"""
        auth_service = AuthService()
        password = "TestPassword123!"
        
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt signature
    
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
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        token = auth_service.generate_access_token(user)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = auth_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["email"] == "test@example.com"
        assert payload["full_name"] == "Test User"
        assert payload["type"] == "access"
        assert "roles" in payload
    
    def test_generate_refresh_token(self):
        """Test JWT refresh token generation"""
        auth_service = AuthService()
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        token = auth_service.generate_refresh_token(user)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = auth_service.decode_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "email" not in payload  # Refresh token has minimal payload
    
    def test_generate_token_pair(self):
        """Test token pair generation"""
        auth_service = AuthService()
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        token_pair = auth_service.generate_token_pair(user)
        
        assert isinstance(token_pair, TokenPair)
        assert token_pair.access_token
        assert token_pair.refresh_token
        assert token_pair.token_type == "bearer"
        assert token_pair.expires_in > 0
        
        # Verify both tokens are valid
        access_payload = auth_service.decode_token(token_pair.access_token)
        refresh_payload = auth_service.decode_token(token_pair.refresh_token)
        
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert access_payload["sub"] == refresh_payload["sub"]
    
    def test_decode_token_valid(self):
        """Test decoding valid token"""
        auth_service = AuthService()
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        token = auth_service.generate_access_token(user)
        payload = auth_service.decode_token(token)
        
        assert payload is not None
        assert isinstance(payload, dict)
        assert "sub" in payload
        assert "iat" in payload
        assert "exp" in payload
    
    def test_decode_token_invalid(self):
        """Test decoding invalid token"""
        auth_service = AuthService()
        
        # Test with malformed token
        payload = auth_service.decode_token("invalid.token.here")
        assert payload is None
        
        # Test with empty token
        payload = auth_service.decode_token("")
        assert payload is None
        
        # Test with completely wrong token
        payload = auth_service.decode_token("not-a-jwt-token")
        assert payload is None
    
    def test_decode_token_expired(self):
        """Test decoding expired token"""
        auth_service = AuthService()
        user_id = uuid4()
        
        # Create an expired token manually
        now = datetime.utcnow()
        payload = {
            "sub": str(user_id),
            "email": "test@example.com",
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),  # Expired 1 hour ago
            "type": "access"
        }
        
        expired_token = jwt.encode(
            payload, 
            auth_service.settings.SECRET_KEY, 
            algorithm=auth_service.settings.ALGORITHM
        )
        
        decoded_payload = auth_service.decode_token(expired_token)
        assert decoded_payload is None
    
    def test_extract_user_claims_valid(self):
        """Test extracting user claims from valid access token"""
        auth_service = AuthService()
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER, Role.VIEWER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        token = auth_service.generate_access_token(user)
        claims = auth_service.extract_user_claims(token)
        
        assert isinstance(claims, UserClaims)
        assert claims.user_id == user_id
        assert claims.email == "test@example.com"
        assert claims.full_name == "Test User"
        assert "user" in claims.roles
        assert "viewer" in claims.roles
    
    def test_extract_user_claims_refresh_token(self):
        """Test extracting user claims from refresh token (should fail)"""
        auth_service = AuthService()
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        refresh_token = auth_service.generate_refresh_token(user)
        claims = auth_service.extract_user_claims(refresh_token)
        
        # Should return None because refresh token doesn't have type="access"
        assert claims is None
    
    def test_extract_user_claims_invalid_token(self):
        """Test extracting user claims from invalid token"""
        auth_service = AuthService()
        
        claims = auth_service.extract_user_claims("invalid.token.here")
        assert claims is None
        
        claims = auth_service.extract_user_claims("")
        assert claims is None
    
    def test_extract_user_claims_malformed_payload(self):
        """Test extracting user claims from token with malformed payload"""
        auth_service = AuthService()
        
        # Create token with missing required fields
        now = datetime.utcnow()
        payload = {
            "sub": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=30),
            "type": "access"
            # Missing email, full_name, roles
        }
        
        malformed_token = jwt.encode(
            payload, 
            auth_service.settings.SECRET_KEY, 
            algorithm=auth_service.settings.ALGORITHM
        )
        
        claims = auth_service.extract_user_claims(malformed_token)
        assert claims is None
    
    def test_token_expiration_times(self):
        """Test that tokens have correct expiration times"""
        auth_service = AuthService()
        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        # Generate tokens
        access_token = auth_service.generate_access_token(user)
        refresh_token = auth_service.generate_refresh_token(user)
        
        # Decode and check expiration
        access_payload = auth_service.decode_token(access_token)
        refresh_payload = auth_service.decode_token(refresh_token)
        
        access_exp = datetime.fromtimestamp(access_payload["exp"])
        refresh_exp = datetime.fromtimestamp(refresh_payload["exp"])
        
        # Access token should expire in ~30 minutes
        access_duration = access_exp - datetime.fromtimestamp(access_payload["iat"])
        assert 25 <= access_duration.total_seconds() / 60 <= 35  # ~30 minutes with some tolerance
        
        # Refresh token should expire in ~7 days
        refresh_duration = refresh_exp - datetime.fromtimestamp(refresh_payload["iat"])
        assert 6.5 <= refresh_duration.days <= 7.5  # ~7 days with some tolerance