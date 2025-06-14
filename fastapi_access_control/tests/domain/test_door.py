import pytest
import time as time_module
from datetime import datetime, timezone, timedelta, time
from uuid import UUID
from app.domain.entities.door import Door, DoorType, SecurityLevel, DoorStatus, AccessSchedule

# Test UUIDs for consistent test data
TEST_DOOR_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d483")
TEST_USER_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

from tests.conftest import SAMPLE_DOOR_UUID, SAMPLE_DOOR_UUID_2

class TestAccessSchedule:
    """Test cases for AccessSchedule value object"""
    
    def test_access_schedule_creation(self):
        """Test AccessSchedule creation with valid data"""
        schedule = AccessSchedule(
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(18, 0)   # 6:00 PM
        )
        
        assert schedule.days_of_week == [0, 1, 2, 3, 4]
        assert schedule.start_time == time(9, 0)
        assert schedule.end_time == time(18, 0)
    
    def test_access_schedule_basic_functionality(self):
        """Test basic AccessSchedule functionality"""
        schedule = AccessSchedule(
            days_of_week=[0, 1, 2, 3, 4],  # Monday to Friday
            start_time=time(9, 0),
            end_time=time(18, 0)
        )
        
        # Test that the schedule is created correctly
        assert schedule.days_of_week == [0, 1, 2, 3, 4]
        assert schedule.start_time == time(9, 0)
        assert schedule.end_time == time(18, 0)
        
        # Test that is_access_allowed_now() can be called without errors
        # We can't easily test the time logic without more complex mocking
        result = schedule.is_access_allowed_now()
        assert isinstance(result, bool)

class TestDoor:
    """Test cases for Door domain entity"""
    
    def test_door_creation(self):
        """Test Door entity creation with valid data"""
        now = datetime.now()
        schedule = AccessSchedule(
            days_of_week=[0, 1, 2, 3, 4],
            start_time=time(9, 0),
            end_time=time(18, 0)
        )
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            description="Main building entrance",
            default_schedule=schedule,
            requires_pin=False,
            max_attempts=3,
            lockout_duration=300,
            failed_attempts=0
        )
        
        assert door.id == TEST_DOOR_ID
        assert door.name == "Main Entrance"
        assert door.location == "Building A"
        assert door.door_type == DoorType.ENTRANCE
        assert door.security_level == SecurityLevel.MEDIUM
        assert door.status == DoorStatus.ACTIVE
        assert door.description == "Main building entrance"
        assert door.default_schedule == schedule
        assert door.requires_pin is False
        assert door.max_attempts == 3
        assert door.lockout_duration == 300
        assert door.failed_attempts == 0
        assert door.last_access is None
        assert door.locked_until is None
    
    def test_door_is_active_with_active_status(self):
        """Test door is_active returns True for ACTIVE status"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        assert door.is_active() is True
    
    def test_door_is_active_with_inactive_status(self):
        """Test door is_active returns False for non-ACTIVE status"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.MAINTENANCE,
            created_at=now,
            updated_at=now
        )
        
        assert door.is_active() is False
    
    def test_door_is_accessible_when_active_and_no_schedule(self):
        """Test door is_accessible returns True when active and no schedule"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            default_schedule=None
        )
        
        assert door.is_accessible() is True
    
    def test_door_is_accessible_when_inactive(self):
        """Test door is_accessible returns False when inactive"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.INACTIVE,
            created_at=now,
            updated_at=now
        )
        
        assert door.is_accessible() is False
    
    def test_door_is_accessible_when_locked_out(self):
        """Test door is_accessible returns False when locked out"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            locked_until=now + timedelta(minutes=5)  # Locked for 5 more minutes
        )
        
        assert door.is_accessible() is False
    
    def test_door_is_locked_out_with_future_locked_until(self):
        """Test is_locked_out returns True when locked_until is in the future"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            locked_until=now + timedelta(minutes=5)
        )
        
        assert door.is_locked_out() is True
    
    def test_door_is_locked_out_with_past_locked_until(self):
        """Test is_locked_out returns False when locked_until is in the past"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            locked_until=now - timedelta(minutes=5)  # Was locked but not anymore
        )
        
        assert door.is_locked_out() is False
    
    def test_door_is_high_security(self):
        """Test is_high_security returns True for HIGH and CRITICAL levels"""
        now = datetime.now()
        
        high_door = Door(
            id=TEST_DOOR_ID,
            name="High Security Door",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.HIGH,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        critical_door = Door(
            id=SAMPLE_DOOR_UUID_2,
            name="Critical Security Door",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.CRITICAL,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        medium_door = Door(
            id=3,
            name="Medium Security Door",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        assert high_door.is_high_security() is True
        assert critical_door.is_high_security() is True
        assert medium_door.is_high_security() is False
    
    def test_door_requires_master_access(self):
        """Test requires_master_access returns True only for CRITICAL level"""
        now = datetime.now()
        
        critical_door = Door(
            id=TEST_DOOR_ID,
            name="Critical Security Door",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.CRITICAL,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        high_door = Door(
            id=SAMPLE_DOOR_UUID_2,
            name="High Security Door",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.HIGH,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        assert critical_door.requires_master_access() is True
        assert high_door.requires_master_access() is False
    
    def test_door_record_successful_access(self):
        """Test record_successful_access updates door state"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            failed_attempts=2,
            locked_until=now + timedelta(minutes=5)
        )
        
        original_updated_at = door.updated_at
        
        # Add small delay to ensure timestamp difference
        time_module.sleep(0.001)
        door.record_successful_access(user_id=TEST_USER_ID)
        
        assert door.last_access is not None
        assert door.failed_attempts == 0
        assert door.locked_until is None
        assert door.updated_at > original_updated_at
    
    def test_door_record_failed_attempt(self):
        """Test record_failed_attempt increments failed attempts"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            failed_attempts=0,
            max_attempts=3,
            lockout_duration=300
        )
        
        original_updated_at = door.updated_at
        
        # Add small delay to ensure timestamp difference
        time_module.sleep(0.001)
        door.record_failed_attempt()
        
        assert door.failed_attempts == 1
        assert door.locked_until is None  # Not locked yet
        assert door.updated_at > original_updated_at
    
    def test_door_record_failed_attempt_triggers_lockout(self):
        """Test record_failed_attempt triggers lockout when max attempts reached"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            failed_attempts=2,  # One away from max
            max_attempts=3,
            lockout_duration=300
        )
        
        door.record_failed_attempt()
        
        assert door.failed_attempts == 3
        assert door.locked_until is not None
        assert door.locked_until > now
    
    def test_door_reset_failed_attempts(self):
        """Test reset_failed_attempts clears failed attempts and lockout"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            failed_attempts=3,
            locked_until=now + timedelta(minutes=5)
        )
        
        original_updated_at = door.updated_at
        
        # Add small delay to ensure timestamp difference
        time_module.sleep(0.001)
        door.reset_failed_attempts()
        
        assert door.failed_attempts == 0
        assert door.locked_until is None
        assert door.updated_at > original_updated_at
    
    def test_door_set_emergency_open(self):
        """Test set_emergency_open changes status to EMERGENCY_OPEN"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        original_updated_at = door.updated_at
        
        # Add small delay to ensure timestamp difference
        time_module.sleep(0.001)
        door.set_emergency_open()
        
        assert door.status == DoorStatus.EMERGENCY_OPEN
        assert door.updated_at > original_updated_at
    
    def test_door_set_emergency_locked(self):
        """Test set_emergency_locked changes status to EMERGENCY_LOCKED"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        original_updated_at = door.updated_at
        
        # Add small delay to ensure timestamp difference
        time_module.sleep(0.001)
        door.set_emergency_locked()
        
        assert door.status == DoorStatus.EMERGENCY_LOCKED
        assert door.updated_at > original_updated_at
    
    def test_door_set_maintenance_mode(self):
        """Test set_maintenance_mode changes status to MAINTENANCE"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        original_updated_at = door.updated_at
        
        # Add small delay to ensure timestamp difference
        time_module.sleep(0.001)
        door.set_maintenance_mode()
        
        assert door.status == DoorStatus.MAINTENANCE
        assert door.updated_at > original_updated_at
    
    def test_door_activate(self):
        """Test activate changes status to ACTIVE and resets failed attempts"""
        now = datetime.now()
        
        door = Door(
            id=TEST_DOOR_ID,
            name="Main Entrance",
            location="Building A",
            door_type=DoorType.ENTRANCE,
            security_level=SecurityLevel.MEDIUM,
            status=DoorStatus.MAINTENANCE,
            created_at=now,
            updated_at=now,
            failed_attempts=3,
            locked_until=now + timedelta(minutes=5)
        )
        
        original_updated_at = door.updated_at
        
        # Add small delay to ensure timestamp difference
        time_module.sleep(0.001)
        door.activate()
        
        assert door.status == DoorStatus.ACTIVE
        assert door.failed_attempts == 0
        assert door.locked_until is None
        assert door.updated_at > original_updated_at