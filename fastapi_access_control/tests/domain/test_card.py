import pytest
import time
from datetime import datetime, timezone, timedelta
from uuid import UUID
from app.domain.entities.card import Card, CardType, CardStatus

# Test UUIDs for consistent test data
TEST_CARD_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d481")
TEST_USER_ID = UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

class TestCard:
    """Test cases for Card domain entity"""
    
    def test_card_creation(self):
        """
        Verifies that a Card instance is correctly created with valid attributes and initial state.
        """
        now = datetime.now()
        valid_until = now + timedelta(days=365)
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now,
            valid_until=valid_until,
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.id == TEST_CARD_ID
        assert card.card_id == "CARD001"
        assert card.user_id == TEST_USER_ID
        assert card.card_type == CardType.EMPLOYEE
        assert card.status == CardStatus.ACTIVE
        assert card.valid_from == now
        assert card.valid_until == valid_until
        assert card.use_count == 0
        assert card.last_used is None
    
    def test_card_is_active_with_active_status(self):
        """
        Tests that a card with ACTIVE status and a valid date range is considered active.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_active() is True
    
    def test_card_is_active_with_inactive_status(self):
        """
        Verifies that is_active() returns False when the card status is INACTIVE.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_active() is False
    
    def test_card_is_active_with_future_valid_from(self):
        """
        Tests that a card with a future valid_from date is not considered active.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now + timedelta(days=1),  # Future date
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_active() is False
    
    def test_card_is_active_with_past_valid_until(self):
        """
        Tests that is_active() returns False when the card's valid_until date is in the past.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=365),
            valid_until=now - timedelta(days=1),  # Past date
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_active() is False
    
    def test_card_is_expired_with_past_valid_until(self):
        """Test card is_expired returns True if valid_until is in the past"""
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=365),
            valid_until=now - timedelta(days=1),  # Past date
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_expired() is True
    
    def test_card_is_expired_with_no_valid_until(self):
        """Test card is_expired returns False if valid_until is None"""
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=None,  # No expiration
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_expired() is False
    
    def test_card_can_access_when_active_and_not_expired(self):
        """Test card can_access returns True when card is active and not expired"""
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.can_access() is True
    
    def test_card_can_access_when_inactive(self):
        """
        Verifies that can_access() returns False for a card with inactive status.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.can_access() is False
    
    def test_card_is_master_card_with_master_type(self):
        """
        Verifies that is_master_card() returns True for an active card of type MASTER.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="MASTER001",
            user_id=TEST_USER_ID,
            card_type=CardType.MASTER,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_master_card() is True
    
    def test_card_is_master_card_with_master_type_but_inactive(self):
        """
        Tests that is_master_card() returns False for a MASTER type card when its status is inactive.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="MASTER001",
            user_id=TEST_USER_ID,
            card_type=CardType.MASTER,
            status=CardStatus.INACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_master_card() is False
    
    def test_card_is_temporary_card(self):
        """Test is_temporary_card returns True for TEMPORARY type"""
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="TEMP001",
            user_id=TEST_USER_ID,
            card_type=CardType.TEMPORARY,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=1),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        assert card.is_temporary_card() is True
    
    def test_card_record_usage(self):
        """
        Verifies that calling record_usage() on a Card updates last_used, increments use_count, and updates updated_at.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        original_use_count = card.use_count
        original_updated_at = card.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        card.record_usage()
        
        assert card.use_count == original_use_count + 1
        assert card.last_used is not None
        assert card.updated_at > original_updated_at
    
    def test_card_suspend(self):
        """
        Tests that suspending a card sets its status to SUSPENDED and updates the updated_at timestamp.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        original_updated_at = card.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        card.suspend()
        
        assert card.status == CardStatus.SUSPENDED
        assert card.updated_at > original_updated_at
    
    def test_card_activate(self):
        """
        Verifies that activating a suspended card sets its status to ACTIVE and updates the updated_at timestamp.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.SUSPENDED,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        original_updated_at = card.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        card.activate()
        
        assert card.status == CardStatus.ACTIVE
        assert card.updated_at > original_updated_at
    
    def test_card_mark_as_lost(self):
        """
        Verifies that calling mark_as_lost() sets the card status to LOST and updates the updated_at timestamp.
        """
        now = datetime.now()
        
        card = Card(
            id=TEST_CARD_ID,
            card_id="CARD001",
            user_id=TEST_USER_ID,
            card_type=CardType.EMPLOYEE,
            status=CardStatus.ACTIVE,
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=365),
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        original_updated_at = card.updated_at
        
        # Add small delay to ensure timestamp difference
        time.sleep(0.001)
        card.mark_as_lost()
        
        assert card.status == CardStatus.LOST
        assert card.updated_at > original_updated_at