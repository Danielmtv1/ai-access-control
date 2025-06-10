"""
Tests for auth value objects
"""
import pytest
from uuid import UUID, uuid4
from pydantic import ValidationError

from app.domain.value_objects.auth import Email, Password, UserClaims, TokenPair


class TestEmail:
    """Tests for Email value object"""
    
    def test_email_valid(self):
        """Test valid email creation"""
        email = Email.create("test@example.com")
        assert str(email) == "test@example.com"
        assert email.value == "test@example.com"
    
    def test_email_invalid_format(self):
        """Test invalid email format"""
        with pytest.raises(ValidationError):
            Email.create("not-an-email")
        
        with pytest.raises(ValidationError):
            Email.create("missing@")
        
        with pytest.raises(ValidationError):
            Email.create("@missing.com")
    
    def test_email_empty(self):
        """Test empty email"""
        with pytest.raises(ValidationError):
            Email.create("")
    
    def test_email_none(self):
        """Test None email"""
        with pytest.raises(ValidationError):
            Email.create(None)


class TestPassword:
    """Tests for Password value object"""
    
    def test_password_valid(self):
        """Test valid password creation"""
        password = Password.create("ValidPass123!")
        assert str(password) == "ValidPass123!"
        assert password.value == "ValidPass123!"
    
    def test_password_too_short(self):
        """Test password too short"""
        with pytest.raises(ValidationError) as exc_info:
            Password.create("Short1!")
        
        assert "at least 8 characters long" in str(exc_info.value)
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            Password.create("lowercase123!")
        
        assert "uppercase letter" in str(exc_info.value)
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            Password.create("UPPERCASE123!")
        
        assert "lowercase letter" in str(exc_info.value)
    
    def test_password_no_number(self):
        """Test password without number"""
        with pytest.raises(ValidationError) as exc_info:
            Password.create("NoNumbers!")
        
        assert "at least one number" in str(exc_info.value)
    
    def test_password_no_special_char(self):
        """Test password without special character"""
        with pytest.raises(ValidationError) as exc_info:
            Password.create("NoSpecial123")
        
        assert "special character" in str(exc_info.value)
    
    def test_password_empty(self):
        """Test empty password"""
        with pytest.raises(ValidationError):
            Password.create("")
    
    def test_password_all_requirements(self):
        """Test password meeting all requirements"""
        valid_passwords = [
            "ValidPass123!",
            "SecurePassword1@",
            "MyP@ssw0rd",
            "Str0ngP@ssw0rd!"
        ]
        
        for pwd in valid_passwords:
            password = Password.create(pwd)
            assert password.value == pwd


class TestUserClaims:
    """Tests for UserClaims value object"""
    
    def test_user_claims_creation(self):
        """Test UserClaims creation"""
        user_id = uuid4()
        claims = UserClaims(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            roles=["user", "viewer"]
        )
        
        assert claims.user_id == user_id
        assert claims.email == "test@example.com"
        assert claims.full_name == "Test User"
        assert claims.roles == ["user", "viewer"]
    
    def test_user_claims_has_role(self):
        """Test has_role method"""
        user_id = uuid4()
        claims = UserClaims(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            roles=["user", "viewer"]
        )
        
        assert claims.has_role("user") is True
        assert claims.has_role("viewer") is True
        assert claims.has_role("admin") is False
        assert claims.has_role("operator") is False
    
    def test_user_claims_has_any_role(self):
        """Test has_any_role method"""
        user_id = uuid4()
        claims = UserClaims(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            roles=["user", "viewer"]
        )
        
        assert claims.has_any_role(["user", "admin"]) is True
        assert claims.has_any_role(["viewer", "operator"]) is True
        assert claims.has_any_role(["admin", "operator"]) is False
        assert claims.has_any_role([]) is False
    
    def test_user_claims_empty_roles(self):
        """Test UserClaims with empty roles"""
        user_id = uuid4()
        claims = UserClaims(
            user_id=user_id,
            email="test@example.com",
            full_name="Test User",
            roles=[]
        )
        
        assert claims.has_role("user") is False
        assert claims.has_any_role(["user", "admin"]) is False
    
    def test_user_claims_invalid_user_id(self):
        """Test UserClaims with invalid user_id"""
        with pytest.raises(ValidationError):
            UserClaims(
                user_id="not-a-uuid",
                email="test@example.com",
                full_name="Test User",
                roles=["user"]
            )


class TestTokenPair:
    """Tests for TokenPair value object"""
    
    def test_token_pair_creation(self):
        """Test TokenPair creation"""
        token_pair = TokenPair(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ",
            refresh_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ",
            expires_in=1800
        )
        
        assert token_pair.access_token
        assert token_pair.refresh_token
        assert token_pair.token_type == "bearer"
        assert token_pair.expires_in == 1800
    
    def test_token_pair_default_values(self):
        """Test TokenPair default values"""
        token_pair = TokenPair(
            access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ",
            refresh_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
        )
        
        assert token_pair.token_type == "bearer"
        assert token_pair.expires_in == 1800  # Default 30 minutes
    
    def test_token_pair_invalid_token_format(self):
        """Test TokenPair with invalid token format"""
        with pytest.raises(ValidationError) as exc_info:
            TokenPair(
                access_token="invalid-token",
                refresh_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
            )
        
        assert "Invalid token format" in str(exc_info.value)
    
    def test_token_pair_empty_token(self):
        """Test TokenPair with empty token"""
        with pytest.raises(ValidationError):
            TokenPair(
                access_token="",
                refresh_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
            )
    
    def test_token_pair_expires_in_too_short(self):
        """Test TokenPair with expires_in too short"""
        with pytest.raises(ValidationError) as exc_info:
            TokenPair(
                access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ",
                refresh_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ",
                expires_in=30
            )
        
        assert "at least 60 seconds" in str(exc_info.value)
    
    def test_token_pair_expires_in_too_long(self):
        """Test TokenPair with expires_in too long"""
        with pytest.raises(ValidationError) as exc_info:
            TokenPair(
                access_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ",
                refresh_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWV9.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ",
                expires_in=100000  # More than 24 hours
            )
        
        assert "cannot exceed 24 hours" in str(exc_info.value)