from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from ..domain.entities.card import Card

class CardRepositoryPort(ABC):
    """Port for Card repository operations"""
    
    @abstractmethod
    async def create(self, card: Card) -> Card:
        """Create a new card"""
        pass
    
    @abstractmethod
    async def get_by_id(self, card_id: UUID) -> Optional[Card]:
        """Get card by ID"""
        pass
    
    @abstractmethod
    async def get_by_card_id(self, card_id: str) -> Optional[Card]:
        """Get card by physical card ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[Card]:
        """Get all cards for a user"""
        pass
    
    @abstractmethod
    async def update(self, card: Card) -> Card:
        """Update existing card"""
        pass
    
    @abstractmethod
    async def delete(self, card_id: UUID) -> bool:
        """Delete card by ID"""
        pass
    
    @abstractmethod
    async def list_cards(self, skip: int = 0, limit: int = 100) -> List[Card]:
        """List cards with pagination"""
        pass
    
    @abstractmethod
    async def get_active_cards(self) -> List[Card]:
        """Get all active cards"""
        pass