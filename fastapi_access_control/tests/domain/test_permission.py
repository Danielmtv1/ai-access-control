import pytest
import time
from datetime import datetime, timezone, timedelta
from uuid import UUID
from app.domain.entities.permission import Permission, PermissionStatus

# Test UUIDs for consistent test data
TEST_PERMISSION_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d485")
TEST_USER_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")
TEST_DOOR_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d483")
TEST_CARD_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d481")

class TestPermission:
    """Test cases for Permission domain entity"""
    
    def test_permission_creation(self):
        """
        Verifies that a Permission entity is correctly created with valid attributes.
        
        Asserts that all fields, including IDs, status, validity dates, access schedule, and pin requirement, are properly assigned, and that last_used is initially None.
        """
        now = datetime.now()
        valid_until = now + timedelta(days=30)
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now,
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            card_id=TEST_CARD_ID,
            valid_until=valid_until,
            access_schedule='{"days": [0,1,2,3,4], "start": "09:00", "end": "18:00"}',
            pin_required=False
        )
        
        assert permission.id == TEST_PERMISSION_ID
        assert permission.user_id == TEST_USER_ID
        assert permission.door_id == TEST_DOOR_ID
        assert permission.card_id == TEST_CARD_ID
        assert permission.status == PermissionStatus.ACTIVE
        assert permission.valid_from == now
        assert permission.valid_until == valid_until
        assert permission.access_schedule == '{"days": [0,1,2,3,4], "start": "09:00", "end": "18:00"}'
        assert permission.pin_required is False
        assert permission.created_by == TEST_USER_ID
        assert permission.last_used is None
    
    def test_permission_is_active_with_active_status(self):
        """
        Verifies that a permission with ACTIVE status and a current validity period is considered active.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.is_active() is True
    
    def test_permission_is_active_with_inactive_status(self):
        """
        Verifies that is_active() returns False when the permission status is INACTIVE, regardless of validity dates.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.is_active() is False
    
    def test_permission_is_active_with_future_valid_from(self):
        """
        Verifies that a permission is not active if its valid_from date is in the future.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now + timedelta(days=1),  # Future date
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.is_active() is False
    
    def test_permission_is_active_with_past_valid_until(self):
        """
        Verifies that a permission is not active when its valid_until date is in the past.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=30),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now - timedelta(days=1)  # Past date
        )
        
        assert permission.is_active() is False
    
    def test_permission_is_expired_with_past_valid_until(self):
        """
        Verifies that is_expired() returns True when the permission's valid_until date is in the past.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=30),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now - timedelta(days=1)  # Past date
        )
        
        assert permission.is_expired() is True
    
    def test_permission_is_expired_with_no_valid_until(self):
        """
        Verifies that a permission with no expiration date (`valid_until` set to None) is not considered expired.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=None  # No expiration
        )
        
        assert permission.is_expired() is False
    
    def test_permission_can_access_door_with_matching_door_id(self):
        """
        Tests that can_access_door returns True when the permission is active and the provided door ID matches the permission's door ID.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_door(door_id=TEST_DOOR_ID) is True
    
    def test_permission_can_access_door_with_non_matching_door_id(self):
        """
        Verifies that can_access_door returns False when the provided door ID does not match the permission's door ID.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_door(door_id=UUID("f47ac10b-58cc-4372-a567-0e02b2c3d484")) is False
    
    def test_permission_can_access_door_when_inactive(self):
        """
        Verifies that can_access_door returns False when the permission status is inactive.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_door(door_id=TEST_DOOR_ID) is False
    
    def test_permission_can_access_with_card_no_specific_card(self):
        """
        Verifies that can_access_with_card returns True when no specific card is required.
        
        This test ensures that a permission with card_id set to None allows access with any card.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            card_id=None,  # No specific card required
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=TEST_CARD_ID) is True
    
    def test_permission_can_access_with_card_matching_card_id(self):
        """Test can_access_with_card returns True when card_id matches"""
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            card_id=TEST_CARD_ID,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=TEST_CARD_ID) is True
    
    def test_permission_can_access_with_card_non_matching_card_id(self):
        """
        Verifies that can_access_with_card returns False when the provided card ID does not match the permission's card ID.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            card_id=TEST_CARD_ID,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=UUID("f47ac10b-58cc-4372-a567-0e02b2c3d482")) is False
    
    def test_permission_can_access_with_card_when_inactive(self):
        """
        Verifies that can_access_with_card returns False when the permission status is inactive.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            card_id=TEST_CARD_ID,
            valid_until=now + timedelta(days=30)
        )
        
        assert permission.can_access_with_card(card_id=TEST_CARD_ID) is False
    
    def test_permission_record_usage(self):
        """
        Verifies that calling record_usage() updates the last_used and updated_at timestamps of a Permission instance.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        original_updated_at = permission.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        permission.record_usage()
        
        assert permission.last_used is not None
        assert permission.updated_at > original_updated_at
    
    def test_permission_suspend(self):
        """
        Verifies that suspending a permission sets its status to SUSPENDED and updates the timestamp.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        original_updated_at = permission.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        permission.suspend()
        
        assert permission.status == PermissionStatus.SUSPENDED
        assert permission.updated_at > original_updated_at
    
    def test_permission_activate(self):
        """
        Verifies that activating a suspended permission sets its status to ACTIVE and updates the updated_at timestamp.
        """
        now = datetime.now()
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.SUSPENDED,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=now + timedelta(days=30)
        )
        
        original_updated_at = permission.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        permission.activate()
        
        assert permission.status == PermissionStatus.ACTIVE
        assert permission.updated_at > original_updated_at
    
    def test_permission_extend_validity(self):
        """
        Verifies that extending a permission's validity updates the valid_until and updated_at fields.
        
        Ensures that calling extend_validity with a new date correctly sets the permission's valid_until to the new value and updates the updated_at timestamp.
        """
        now = datetime.now()
        original_valid_until = now + timedelta(days=30)
        new_valid_until = now + timedelta(days=60)
        
        permission = Permission(
            id=TEST_PERMISSION_ID,
            user_id=TEST_USER_ID,
            door_id=TEST_DOOR_ID,
            status=PermissionStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            created_by=TEST_USER_ID,
            created_at=now,
            updated_at=now,
            valid_until=original_valid_until
        )
        
        original_updated_at = permission.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        permission.extend_validity(new_valid_until)
        
        assert permission.valid_until == new_valid_until
        assert permission.updated_at > original_updated_at