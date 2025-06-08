import pytest
from datetime import datetime, UTC, timedelta
from app.domain.entities.permission import Permission, PermissionStatus

class TestPermission:
    """Test cases for Permission domain entity"""
    
    def test_permission_creation(self):
        """Test Permission entity creation with valid data"""
        now = datetime.now(UTC).replace(tzinfo=None)
        valid_until = now + timedelta(days=30)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now,
            created_by=1,
            created_at=now,
            updated_at=now,
            card_id=1,
            valid_until=valid_until,
            access_schedule='{"days": [0,1,2,3,4], "start": "09:00", "end": "18:00"}',
            pin_required=False
        )
        
        assert permission.id == 1
        assert permission.user_id == 1
        assert permission.door_id == 1
        assert permission.card_id == 1
        assert permission.status == PermissionStatus.ACTIVE
        assert permission.valid_from == now
        assert permission.valid_until == valid_until
        assert permission.access_schedule == '{"days": [0,1,2,3,4], "start": "09:00", "end": "18:00"}'
        assert permission.pin_required is False
        assert permission.created_by == 1
        assert permission.last_used is None
    
    def test_permission_is_active_with_active_status(self):
        """Test permission is_active returns True for ACTIVE status"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.is_active() is True
    
    def test_permission_is_active_with_inactive_status(self):
        """Test permission is_active returns False for INACTIVE status"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.is_active() is False
    
    def test_permission_is_active_with_future_valid_from(self):
        """Test permission is_active returns False if valid_from is in the future"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now + timedelta(days=1),  # Future date
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.is_active() is False
    
    def test_permission_is_active_with_past_valid_until(self):
        """Test permission is_active returns False if valid_until is in the past"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=30),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now - timedelta(days=1)  # Past date
        )
        
        assert permission.is_active() is False
    
    def test_permission_is_expired_with_past_valid_until(self):
        """Test permission is_expired returns True if valid_until is in the past"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=30),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now - timedelta(days=1)  # Past date
        )
        
        assert permission.is_expired() is True
    
    def test_permission_is_expired_with_no_valid_until(self):
        """Test permission is_expired returns False if valid_until is None"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=None  # No expiration
        )
        
        assert permission.is_expired() is False
    
    def test_permission_can_access_door_with_matching_door_id(self):
        """Test can_access_door returns True when permission is active and door_id matches"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_door(door_id=1) is True
    
    def test_permission_can_access_door_with_non_matching_door_id(self):
        """Test can_access_door returns False when door_id doesn't match"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_door(door_id=2) is False
    
    def test_permission_can_access_door_when_inactive(self):
        """Test can_access_door returns False when permission is inactive"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_door(door_id=1) is False
    
    def test_permission_can_access_with_card_no_specific_card(self):
        """Test can_access_with_card returns True when permission has no specific card requirement"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            card_id=None,  # No specific card required
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=123) is True
    
    def test_permission_can_access_with_card_matching_card_id(self):
        """Test can_access_with_card returns True when card_id matches"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            card_id=123,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=123) is True
    
    def test_permission_can_access_with_card_non_matching_card_id(self):
        """Test can_access_with_card returns False when card_id doesn't match"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            card_id=123,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=456) is False
    
    def test_permission_can_access_with_card_when_inactive(self):
        """Test can_access_with_card returns False when permission is inactive"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            card_id=123,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=123) is False
    
    def test_permission_record_usage(self):
        """Test record_usage updates last_used and updated_at"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        original_updated_at = permission.updated_at
        
        permission.record_usage()
        
        assert permission.last_used is not None
        assert permission.updated_at > original_updated_at
    
    def test_permission_suspend(self):
        """Test suspend changes status to SUSPENDED"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        original_updated_at = permission.updated_at
        
        permission.suspend()
        
        assert permission.status == PermissionStatus.SUSPENDED
        assert permission.updated_at > original_updated_at
    
    def test_permission_activate(self):
        """Test activate changes status to ACTIVE"""
        now = datetime.now(UTC).replace(tzinfo=None)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.SUSPENDED,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        original_updated_at = permission.updated_at
        
        permission.activate()
        
        assert permission.status == PermissionStatus.ACTIVE
        assert permission.updated_at > original_updated_at
    
    def test_permission_extend_validity(self):
        """Test extend_validity updates valid_until"""
        now = datetime.now(UTC).replace(tzinfo=None)
        original_valid_until = now + timedelta(days=30)
        new_valid_until = now + timedelta(days=60)
        
        permission = Permission(
            id=1,
            user_id=1,
            door_id=1,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=1,
            created_at=now,
            updated_at=now,
            valid_until=original_valid_until
        )
        
        original_updated_at = permission.updated_at
        
        permission.extend_validity(new_valid_until)
        
        assert permission.valid_until == new_valid_until
        assert permission.updated_at > original_updated_at