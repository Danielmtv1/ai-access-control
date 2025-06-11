from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Callable
from uuid import UUID
from app.ports.card_repository_port import CardRepositoryPort
from app.domain.entities.card import Card, CardStatus
from app.infrastructure.database.models.card import CardModel
from app.infrastructure.persistence.adapters.mappers.card_mapper import CardMapper
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.domain.exceptions import RepositoryError

logger = logging.getLogger(__name__)

class SqlAlchemyCardRepository(CardRepositoryPort):
    """SQLAlchemy implementation of CardRepositoryPort"""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
    
    async def create(self, card: Card) -> Card:
        async with self.session_factory() as db:
            try:
                card_model = CardMapper.to_model(card)
                # Don't set ID for new cards, let DB generate it
                card_model.id = None
                
                db.add(card_model)
                await db.commit()
                await db.refresh(card_model)
                
                return CardMapper.to_domain(card_model)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error creating card: {e}")
                raise RepositoryError(f"Error creating card: {e}") from e
    
    async def get_by_id(self, card_id: UUID) -> Optional[Card]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(CardModel).where(CardModel.id == card_id)
                )
                card_model = result.scalar_one_or_none()
                
                return CardMapper.to_domain(card_model) if card_model else None
            except SQLAlchemyError as e:
                logger.error(f"Database error getting card by ID: {e}")
                raise RepositoryError(f"Error getting card: {e}") from e
    
    async def get_by_card_id(self, card_id: str) -> Optional[Card]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(CardModel).where(CardModel.card_id == card_id)
                )
                card_model = result.scalar_one_or_none()
                logger.info(f"Found card with card_id: {card_id}" if card_model else f"No card found with card_id: {card_id}")
                return CardMapper.to_domain(card_model) if card_model else None
            except SQLAlchemyError as e:
                logger.error(f"Database error getting card by card_id: {e}")
                raise RepositoryError(f"Error getting card: {e}") from e
    
    async def get_by_user_id(self, user_id: UUID) -> List[Card]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(CardModel).where(CardModel.user_id == user_id)
                )
                card_models = result.scalars().all()
                
                return [CardMapper.to_domain(model) for model in card_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error getting cards by user_id: {e}")
                raise RepositoryError(f"Error getting cards: {e}") from e
    
    async def update(self, card: Card) -> Card:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(CardModel).where(CardModel.id == card.id)
                )
                card_model = result.scalar_one_or_none()
                
                if not card_model:
                    raise RepositoryError(f"Card with ID {card.id} not found")
                
                card_model = CardMapper.update_model_from_domain(card_model, card)
                await db.commit()
                await db.refresh(card_model)
                
                return CardMapper.to_domain(card_model)
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error updating card: {e}")
                raise RepositoryError(f"Error updating card: {e}") from e
    
    async def delete(self, card_id: UUID) -> bool:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(CardModel).where(CardModel.id == card_id)
                )
                card_model = result.scalar_one_or_none()
                
                if not card_model:
                    return False
                
                await db.delete(card_model)
                await db.commit()
                return True
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(f"Database error deleting card: {e}")
                raise RepositoryError(f"Error deleting card: {e}") from e
    
    async def list_cards(self, skip: int = 0, limit: int = 100) -> List[Card]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(CardModel).offset(skip).limit(limit)
                )
                card_models = result.scalars().all()
                
                return [CardMapper.to_domain(model) for model in card_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error listing cards: {e}")
                raise RepositoryError(f"Error listing cards: {e}") from e
    
    async def get_active_cards(self) -> List[Card]:
        async with self.session_factory() as db:
            try:
                result = await db.execute(
                    select(CardModel).where(CardModel.status == CardStatus.ACTIVE.value)
                )
                card_models = result.scalars().all()
                
                return [CardMapper.to_domain(model) for model in card_models]
            except SQLAlchemyError as e:
                logger.error(f"Database error getting active cards: {e}")
                raise RepositoryError(f"Error getting active cards: {e}") from e