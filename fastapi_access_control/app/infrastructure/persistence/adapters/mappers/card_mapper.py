from datetime import datetime, timezone
from app.domain.entities.card import Card, CardType, CardStatus
from app.infrastructure.database.models.card import CardModel

class CardMapper:
    """Mapeador entre entidades de dominio Card y modelos de base de datos"""
    
    @staticmethod
    def to_domain(model: CardModel) -> Card:
        """Convierte un modelo de base de datos a una entidad de dominio"""
        if not model:
            return None
            
        return Card(
            id=model.id,
            card_id=model.card_id,
            user_id=model.user_id,
            card_type=CardType(model.card_type),
            status=CardStatus(model.status),
            valid_from=model.valid_from,
            valid_until=model.valid_until,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_used=model.last_used,
            use_count=model.use_count
        )
    
    @staticmethod
    def to_model(card: Card) -> CardModel:
        """Convierte una entidad de dominio a un modelo de base de datos"""
        return CardModel(
            id=card.id,
            card_id=card.card_id,
            user_id=card.user_id,
            card_type=card.card_type.value,
            status=card.status.value,
            valid_from=card.valid_from,
            valid_until=card.valid_until,
            last_used=card.last_used,
            use_count=card.use_count,
            created_at=card.created_at,
            updated_at=card.updated_at
        )
    
    @staticmethod
    def update_model_from_domain(model: CardModel, card: Card) -> CardModel:
        """Actualiza un modelo de base de datos con los datos de una entidad de dominio"""
        model.card_id = card.card_id
        model.user_id = card.user_id
        model.card_type = card.card_type.value
        model.status = card.status.value
        model.valid_from = card.valid_from
        model.valid_until = card.valid_until
        model.last_used = card.last_used
        model.use_count = card.use_count
        model.updated_at = datetime.now(timezone.utc)
        return model