from typing import Optional, List
from datetime import datetime, timezone, UTC
from uuid import UUID
from ...domain.entities.card import Card, CardType, CardStatus
from ...ports.card_repository_port import CardRepositoryPort
from ...ports.user_repository_port import UserRepositoryPort
from ...domain.exceptions import (
    DomainError, CardNotFoundError, UserNotFoundError, EntityAlreadyExistsError
)
import logging

logger = logging.getLogger(__name__)

class CreateCardUseCase:
    """Use case for creating new cards"""
    
    def __init__(self, 
                 card_repository: CardRepositoryPort,
                 user_repository: UserRepositoryPort):
        self.card_repository = card_repository
        self.user_repository = user_repository
    
    async def execute(self, 
                     card_id: str,
                     user_id: UUID,
                     card_type: str,
                     valid_from: datetime,
                     valid_until: Optional[datetime] = None) -> Card:
        """
                     Creates a new card for a user after verifying user existence and card ID uniqueness.
                     
                     Raises:
                         UserNotFoundError: If the specified user does not exist.
                         EntityAlreadyExistsError: If a card with the given card ID already exists.
                     
                     Returns:
                         The newly created Card instance.
                     """
        
        # Check if user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))
        
        # Check if card ID already exists
        existing_card = await self.card_repository.get_by_card_id(card_id)
        if existing_card:
            raise EntityAlreadyExistsError("Card", card_id)
        
        # Create card entity
        now = datetime.now(UTC).replace(tzinfo=None)
        card = Card(
            id=None,  # Will be set by database
            card_id=card_id,
            user_id=user_id,
            card_type=CardType(card_type),
            status=CardStatus.ACTIVE,
            valid_from=valid_from,
            valid_until=valid_until,
            created_at=now,
            updated_at=now,
            use_count=0
        )
        
        logger.info(f"Creating new card {card_id} for user {user_id}")
        return await self.card_repository.create(card)

class GetCardUseCase:
    """Use case for getting card by ID"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, card_id: UUID) -> Card:
        """
        Retrieves a card by its unique identifier.
        
        Args:
            card_id: The UUID of the card to retrieve.
        
        Returns:
            The card associated with the given UUID.
        
        Raises:
            CardNotFoundError: If no card exists with the specified UUID.
        """
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(str(card_id))
        return card

class GetCardByCardIdUseCase:
    """Use case for getting card by physical card ID"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, card_id: str) -> Card:
        """
        Retrieves a card by its physical card ID.
        
        Args:
            card_id: The physical card ID as a string.
        
        Returns:
            The card associated with the given card ID.
        
        Raises:
            CardNotFoundError: If no card with the specified card ID exists.
        """
        card = await self.card_repository.get_by_card_id(card_id)
        if not card:
            raise CardNotFoundError(card_id)
        return card

class GetUserCardsUseCase:
    """Use case for getting all cards for a user"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, user_id: UUID) -> List[Card]:
        """Get all cards for a user"""
        return await self.card_repository.get_by_user_id(user_id)

class UpdateCardUseCase:
    """Use case for updating card"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, 
                     card_id: UUID,
                     card_type: Optional[str] = None,
                     status: Optional[str] = None,
                     valid_until: Optional[datetime] = None) -> Card:
        """
                     Updates an existing card's type, status, or validity end date.
                     
                     Retrieves the card by its UUID and applies any provided updates to the card type, status, or valid_until fields. Converts valid_until to a timezone-naive datetime if necessary and updates the card's updated_at timestamp.
                     
                     Args:
                         card_id: The UUID of the card to update.
                         card_type: Optional new card type.
                         status: Optional new card status.
                         valid_until: Optional new validity end date.
                     
                     Returns:
                         The updated Card instance.
                     
                     Raises:
                         CardNotFoundError: If no card with the given UUID exists.
                     """
        
        # Get existing card
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(str(card_id))
        
        # Update fields if provided
        if card_type:
            card.card_type = CardType(card_type)
        if status:
            card.status = CardStatus(status)
        if valid_until is not None:
            # Convert to timezone-naive if it has timezone info
            if valid_until.tzinfo:
                card.valid_until = valid_until.replace(tzinfo=None)
            else:
                card.valid_until = valid_until
        
        card.updated_at = datetime.now(UTC).replace(tzinfo=None)
        
        logger.info(f"Updating card {card_id}")
        return await self.card_repository.update(card)

class DeactivateCardUseCase:
    """Use case for deactivating card"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, card_id: UUID) -> Card:
        """
        Deactivates a card by setting its status to inactive.
        
        Args:
        	card_id: The UUID of the card to deactivate.
        
        Returns:
        	The updated Card object with status set to inactive.
        
        Raises:
        	CardNotFoundError: If no card exists with the given UUID.
        """
        
        # Get existing card
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(str(card_id))
        
        # Deactivate card
        card.status = CardStatus.INACTIVE
        card.updated_at = datetime.now(UTC).replace(tzinfo=None)
        
        logger.info(f"Deactivating card {card_id}")
        return await self.card_repository.update(card)

class SuspendCardUseCase:
    """Use case for suspending card"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, card_id: UUID) -> Card:
        """
        Suspends a card identified by its UUID.
        
        Raises:
            CardNotFoundError: If no card with the given UUID exists.
        
        Returns:
            The updated Card object after suspension.
        """
        
        # Get existing card
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(str(card_id))
        
        # Suspend card
        card.suspend()
        
        logger.info(f"Suspending card {card_id}")
        return await self.card_repository.update(card)

class ListCardsUseCase:
    """Use case for listing cards with pagination"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, skip: int = 0, limit: int = 100) -> List[Card]:
        """List cards with pagination"""
        return await self.card_repository.list_cards(skip, limit)

class DeleteCardUseCase:
    """Use case for deleting card"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, card_id: UUID) -> bool:
        """
        Deletes a card by its UUID.
        
        Raises:
            CardNotFoundError: If the card with the specified UUID does not exist.
        
        Returns:
            True if the card was successfully deleted, False otherwise.
        """
        
        # Check if card exists
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(str(card_id))
        
        logger.info(f"Deleting card {card_id}")
        return await self.card_repository.delete(card_id)