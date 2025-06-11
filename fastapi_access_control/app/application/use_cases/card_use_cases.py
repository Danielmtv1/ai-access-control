from typing import Optional, List
from datetime import datetime, timezone, UTC
from uuid import UUID
from ...domain.entities.card import Card, CardType, CardStatus
from ...ports.card_repository_port import CardRepositoryPort
from ...ports.user_repository_port import UserRepositoryPort
from ...domain.exceptions import DomainError
import logging

logger = logging.getLogger(__name__)

class CardNotFoundError(DomainError):
    """Card not found error"""
    pass

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
        """Create new card"""
        
        # Check if user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise DomainError(f"User with ID {user_id} not found")
        
        # Check if card ID already exists
        existing_card = await self.card_repository.get_by_card_id(card_id)
        if existing_card:
            raise DomainError(f"Card with ID {card_id} already exists")
        
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
        """Get card by ID"""
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(f"Card with ID {card_id} not found")
        return card

class GetCardByCardIdUseCase:
    """Use case for getting card by physical card ID"""
    
    def __init__(self, card_repository: CardRepositoryPort):
        self.card_repository = card_repository
    
    async def execute(self, card_id: str) -> Card:
        """Get card by physical card ID"""
        card = await self.card_repository.get_by_card_id(card_id)
        if not card:
            raise CardNotFoundError(f"Card with card_id {card_id} not found")
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
        """Update card"""
        
        # Get existing card
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(f"Card with ID {card_id} not found")
        
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
        """Deactivate card"""
        
        # Get existing card
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(f"Card with ID {card_id} not found")
        
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
        """Suspend card"""
        
        # Get existing card
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(f"Card with ID {card_id} not found")
        
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
        """Delete card"""
        
        # Check if card exists
        card = await self.card_repository.get_by_id(card_id)
        if not card:
            raise CardNotFoundError(f"Card with ID {card_id} not found")
        
        logger.info(f"Deleting card {card_id}")
        return await self.card_repository.delete(card_id)