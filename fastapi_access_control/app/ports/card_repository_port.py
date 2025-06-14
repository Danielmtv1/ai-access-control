from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from ..domain.entities.card import Card

class CardRepositoryPort(ABC):
    """Port for Card repository operations"""
    
    @abstractmethod
    async def create(self, card: Card) -> Card:
        """
        Creates a new card entity.
        
        Args:
        	card: The card entity to be created.
        
        Returns:
        	The created card entity.
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, card_id: UUID) -> Optional[Card]:
        """
        Retrieves a card by its unique UUID.
        
        Args:
            card_id: The UUID of the card to retrieve.
        
        Returns:
            The card with the specified UUID, or None if not found.
        """
        pass
    
    @abstractmethod
    async def get_by_card_id(self, card_id: str) -> Optional[Card]:
        """
        Retrieves a card entity by its physical card ID.
        
        Args:
            card_id: The physical card identifier as a string.
        
        Returns:
            The corresponding Card object if found, otherwise None.
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[Card]:
        """
        Retrieves all cards associated with a specific user.
        
        Args:
            user_id: The UUID of the user whose cards are to be retrieved.
        
        Returns:
            A list of Card objects belonging to the specified user.
        """
        pass
    
    @abstractmethod
    async def update(self, card: Card) -> Card:
        """
        Updates an existing card entity.
        
        Args:
        	card: The card object containing updated information.
        
        Returns:
        	The updated card entity.
        """
        pass
    
    @abstractmethod
    async def delete(self, card_id: UUID) -> bool:
        """
        Deletes a card by its unique UUID.
        
        Args:
        	card_id: The UUID of the card to delete.
        
        Returns:
        	True if the card was successfully deleted, False otherwise.
        """
        pass
    
    @abstractmethod
    async def list_cards(self, skip: int = 0, limit: int = 100) -> List[Card]:
        """List cards with pagination"""
        pass
    
    @abstractmethod
    async def get_active_cards(self) -> List[Card]:
        """Get all active cards"""
        pass