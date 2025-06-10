from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

class CardType(Enum):
    EMPLOYEE = "employee"
    VISITOR = "visitor"
    CONTRACTOR = "contractor"
    MASTER = "master"
    TEMPORARY = "temporary"

class CardStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOST = "lost"
    EXPIRED = "expired"

@dataclass
class Card:
    """Domain entity for Card - Clean domain logic"""
    id: UUID
    card_id: str  # Physical card identifier (RFID, NFC, etc.)
    user_id: UUID
    card_type: CardType
    status: CardStatus
    valid_from: datetime
    valid_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    use_count: int
    last_used: Optional[datetime] = None
    
    def is_active(self) -> bool:
        """Business logic: Card can be used for access"""
        if self.status != CardStatus.ACTIVE:
            return False
        
        now = datetime.now()
        if now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
            
        return True
    
    def is_expired(self) -> bool:
        """Business logic: Check if card is expired"""
        if not self.valid_until:
            return False
        return datetime.now() > self.valid_until
    
    def can_access(self) -> bool:
        """Business logic: Card can be used for access validation"""
        return self.is_active() and not self.is_expired()
    
    def is_master_card(self) -> bool:
        """Business logic: Master card has special privileges"""
        return self.card_type == CardType.MASTER and self.is_active()
    
    def is_temporary_card(self) -> bool:
        """Business logic: Temporary card with time restrictions"""
        return self.card_type == CardType.TEMPORARY
    
    def record_usage(self) -> None:
        """Business logic: Record card usage"""
        self.last_used = datetime.now()
        self.use_count += 1
        self.updated_at = datetime.now()
    
    def suspend(self) -> None:
        """Business logic: Suspend card access"""
        self.status = CardStatus.SUSPENDED
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Business logic: Activate card"""
        self.status = CardStatus.ACTIVE
        self.updated_at = datetime.now()
    
    def mark_as_lost(self) -> None:
        """Business logic: Mark card as lost"""
        self.status = CardStatus.LOST
        self.updated_at = datetime.now()