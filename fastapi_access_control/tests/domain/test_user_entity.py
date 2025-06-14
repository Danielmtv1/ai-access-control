"""
Tests for User entity
"""
import pytest
from datetime import datetime, timezone, UTC
from uuid import UUID, uuid4

from app.domain.entities.user import User, Role, UserStatus
from tests.conftest import SAMPLE_USER_UUID, SAMPLE_CARD_UUID, SAMPLE_CARD_UUID_2, SAMPLE_DOOR_UUID, SAMPLE_DOOR_UUID_2


class TestUser:
    """Tests for User entity"""
    
    @pytest.fixture
    def sample_user(self):
        """Sample user for testing"""
        return User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            roles=[Role.USER],
            status=UserStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
    
    def test_user_creation(self, sample_user):
        """Test user entity creation"""
        assert isinstance(sample_user.id, UUID)
        assert sample_user.email == "test@example.com"
        assert sample_user.full_name == "Test User"
        assert Role.USER in sample_user.roles
        assert sample_user.status == UserStatus.ACTIVE
        assert sample_user.last_login is None
    
    def test_is_active_with_active_status(self, sample_user):
        """Test is_active with active status"""
        sample_user.status = UserStatus.ACTIVE
        assert sample_user.is_active() is True
    
    def test_is_active_with_inactive_status(self, sample_user):
        """Test is_active with inactive status"""
        sample_user.status = UserStatus.INACTIVE
        assert sample_user.is_active() is False
    
    def test_is_active_with_suspended_status(self, sample_user):
        """Test is_active with suspended status"""
        sample_user.status = UserStatus.SUSPENDED
        assert sample_user.is_active() is False
    
    def test_has_role_single_role(self, sample_user):
        """Test has_role with single role"""
        sample_user.roles = [Role.USER]
        
        assert sample_user.has_role(Role.USER) is True
        assert sample_user.has_role(Role.ADMIN) is False
        assert sample_user.has_role(Role.OPERATOR) is False
        assert sample_user.has_role(Role.VIEWER) is False
    
    def test_has_role_multiple_roles(self, sample_user):
        """Test has_role with multiple roles"""
        sample_user.roles = [Role.USER, Role.VIEWER, Role.OPERATOR]
        
        assert sample_user.has_role(Role.USER) is True
        assert sample_user.has_role(Role.VIEWER) is True
        assert sample_user.has_role(Role.OPERATOR) is True
        assert sample_user.has_role(Role.ADMIN) is False
    
    def test_has_role_empty_roles(self, sample_user):
        """Test has_role with empty roles"""
        sample_user.roles = []
        
        assert sample_user.has_role(Role.USER) is False
        assert sample_user.has_role(Role.ADMIN) is False
    
    def test_has_any_role_match(self, sample_user):
        """Test has_any_role with matching roles"""
        sample_user.roles = [Role.USER, Role.VIEWER]
        
        assert sample_user.has_any_role([Role.USER, Role.ADMIN]) is True
        assert sample_user.has_any_role([Role.VIEWER, Role.OPERATOR]) is True
        assert sample_user.has_any_role([Role.USER]) is True
    
    def test_has_any_role_no_match(self, sample_user):
        """Test has_any_role with no matching roles"""
        sample_user.roles = [Role.USER, Role.VIEWER]
        
        assert sample_user.has_any_role([Role.ADMIN, Role.OPERATOR]) is False
    
    def test_has_any_role_empty_check_list(self, sample_user):
        """Test has_any_role with empty check list"""
        sample_user.roles = [Role.USER]
        
        assert sample_user.has_any_role([]) is False
    
    def test_has_any_role_empty_user_roles(self, sample_user):
        """Test has_any_role with empty user roles"""
        sample_user.roles = []
        
        assert sample_user.has_any_role([Role.USER, Role.ADMIN]) is False
    
    def test_can_access_admin_panel_admin_active(self, sample_user):
        """Test admin panel access for active admin"""
        sample_user.roles = [Role.ADMIN]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_access_admin_panel() is True
    
    def test_can_access_admin_panel_admin_inactive(self, sample_user):
        """Test admin panel access for inactive admin"""
        sample_user.roles = [Role.ADMIN]
        sample_user.status = UserStatus.INACTIVE
        
        assert sample_user.can_access_admin_panel() is False
    
    def test_can_access_admin_panel_non_admin(self, sample_user):
        """Test admin panel access for non-admin"""
        sample_user.roles = [Role.USER]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_access_admin_panel() is False
    
    def test_can_access_admin_panel_operator(self, sample_user):
        """Test admin panel access for operator (should be false)"""
        sample_user.roles = [Role.OPERATOR]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_access_admin_panel() is False
    
    def test_can_manage_devices_admin(self, sample_user):
        """Test device management for admin"""
        sample_user.roles = [Role.ADMIN]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_manage_devices() is True
    
    def test_can_manage_devices_operator(self, sample_user):
        """Test device management for operator"""
        sample_user.roles = [Role.OPERATOR]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_manage_devices() is True
    
    def test_can_manage_devices_user(self, sample_user):
        """Test device management for regular user"""
        sample_user.roles = [Role.USER]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_manage_devices() is False
    
    def test_can_manage_devices_viewer(self, sample_user):
        """Test device management for viewer"""
        sample_user.roles = [Role.VIEWER]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_manage_devices() is False
    
    def test_can_manage_devices_inactive(self, sample_user):
        """Test device management for inactive admin"""
        sample_user.roles = [Role.ADMIN]
        sample_user.status = UserStatus.INACTIVE
        
        assert sample_user.can_manage_devices() is False
    
    def test_can_view_access_logs_admin(self, sample_user):
        """Test access log viewing for admin"""
        sample_user.roles = [Role.ADMIN]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_view_access_logs() is True
    
    def test_can_view_access_logs_operator(self, sample_user):
        """Test access log viewing for operator"""
        sample_user.roles = [Role.OPERATOR]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_view_access_logs() is True
    
    def test_can_view_access_logs_viewer(self, sample_user):
        """Test access log viewing for viewer"""
        sample_user.roles = [Role.VIEWER]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_view_access_logs() is True
    
    def test_can_view_access_logs_user(self, sample_user):
        """Test access log viewing for regular user"""
        sample_user.roles = [Role.USER]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_view_access_logs() is False
    
    def test_can_view_access_logs_inactive(self, sample_user):
        """Test access log viewing for inactive viewer"""
        sample_user.roles = [Role.VIEWER]
        sample_user.status = UserStatus.INACTIVE
        
        assert sample_user.can_view_access_logs() is False
    
    def test_user_with_multiple_roles_permissions(self, sample_user):
        """Test user with multiple roles has all permissions"""
        sample_user.roles = [Role.ADMIN, Role.OPERATOR, Role.VIEWER]
        sample_user.status = UserStatus.ACTIVE
        
        assert sample_user.can_access_admin_panel() is True
        assert sample_user.can_manage_devices() is True
        assert sample_user.can_view_access_logs() is True
    
    def test_user_last_login_optional(self, sample_user):
        """Test that last_login is optional"""
        assert sample_user.last_login is None
        
        # Set last login
        now = datetime.now(UTC)
        sample_user.last_login = now
        assert sample_user.last_login == now


class TestUserStatus:
    """Tests for UserStatus enum"""
    
    def test_user_status_values(self):
        """Test UserStatus enum values"""
        assert UserStatus.ACTIVE.value == "active"
        assert UserStatus.INACTIVE.value == "inactive"
        assert UserStatus.SUSPENDED.value == "suspended"
    
    def test_user_status_from_value(self):
        """Test creating UserStatus from value"""
        assert UserStatus("active") == UserStatus.ACTIVE
        assert UserStatus("inactive") == UserStatus.INACTIVE
        assert UserStatus("suspended") == UserStatus.SUSPENDED


class TestRole:
    """Tests for Role enum"""
    
    def test_role_values(self):
        """Test Role enum values"""
        assert Role.ADMIN.value == "admin"
        assert Role.OPERATOR.value == "operator"
        assert Role.USER.value == "user"
        assert Role.VIEWER.value == "viewer"
    
    def test_role_from_value(self):
        """Test creating Role from value"""
        assert Role("admin") == Role.ADMIN
        assert Role("operator") == Role.OPERATOR
        assert Role("user") == Role.USER
        assert Role("viewer") == Role.VIEWER