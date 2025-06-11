from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID

class CardTypeEnum(str, Enum):
    EMPLOYEE = "employee"
    VISITOR = "visitor"
    CONTRACTOR = "contractor"
    MASTER = "master"
    TEMPORARY = "temporary"

class CardStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOST = "lost"
    EXPIRED = "expired"

class CreateCardRequest(BaseModel):
    """Request model for creating a new card"""
    card_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Physical card identifier (RFID, NFC, etc.)",
        example="CARD001234"
    )
    user_id: UUID = Field(
        ...,
        description="UUID of the user this card belongs to",
        example="f190a1ef-8ddd-47c5-ae99-04c574601e31"
    )
    card_type: CardTypeEnum = Field(
        ...,
        description="Type of card",
        example=CardTypeEnum.EMPLOYEE
    )
    valid_from: datetime = Field(
        ...,
        description="Date and time when the card becomes valid",
        example="2024-01-01T00:00:00"
    )
    valid_until: Optional[datetime] = Field(
        None,
        description="Date and time when the card expires (null for no expiration)",
        example="2024-12-31T23:59:59"
    )

    @validator('valid_until')
    def validate_valid_until(cls, v, values):
        if v and 'valid_from' in values and v <= values['valid_from']:
            raise ValueError('valid_until must be after valid_from')
        return v

    class Config:
        schema_extra = {
            "example": {
                "card_id": "CARD001234",
                "user_id": "f190a1ef-8ddd-47c5-ae99-04c574601e31",
                "card_type": "employee",
                "valid_from": "2024-01-01T00:00:00",
                "valid_until": "2024-12-31T23:59:59"
            }
        }

class UpdateCardRequest(BaseModel):
    """Request model for updating a card"""
    card_type: Optional[CardTypeEnum] = Field(
        None,
        description="Type of card"
    )
    status: Optional[CardStatusEnum] = Field(
        None,
        description="Status of the card"
    )
    valid_until: Optional[datetime] = Field(
        None,
        description="Date and time when the card expires"
    )

    class Config:
        schema_extra = {
            "example": {
                "card_type": "employee",
                "status": "active",
                "valid_until": "2024-12-31T23:59:59"
            }
        }

class CardResponse(BaseModel):
    """Response model for card data"""
    id: UUID = Field(..., description="Card database UUID", example="a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    card_id: str = Field(..., description="Physical card identifier", example="CARD001234")
    user_id: UUID = Field(..., description="UUID of the user this card belongs to", example="f190a1ef-8ddd-47c5-ae99-04c574601e31")
    card_type: CardTypeEnum = Field(..., description="Type of card", example=CardTypeEnum.EMPLOYEE)
    status: CardStatusEnum = Field(..., description="Status of the card", example=CardStatusEnum.ACTIVE)
    valid_from: datetime = Field(..., description="Date when card becomes valid", example="2024-01-01T00:00:00")
    valid_until: Optional[datetime] = Field(None, description="Date when card expires", example="2024-12-31T23:59:59")
    last_used: Optional[datetime] = Field(None, description="Last time card was used", example="2024-06-01T10:30:00")
    use_count: int = Field(..., description="Number of times card has been used", example=42)
    created_at: datetime = Field(..., description="Date when card was created", example="2024-01-01T00:00:00")
    updated_at: datetime = Field(..., description="Date when card was last updated", example="2024-06-01T10:30:00")

    @classmethod
    def from_entity(cls, card) -> 'CardResponse':
        """Create CardResponse from Card entity"""
        return cls(
            id=card.id,
            card_id=card.card_id,
            user_id=card.user_id,
            card_type=card.card_type,
            status=card.status,
            valid_from=card.valid_from,
            valid_until=card.valid_until,
            last_used=card.last_used,
            use_count=card.use_count,
            created_at=card.created_at,
            updated_at=card.updated_at
        )

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "card_id": "CARD001234",
                "user_id": "f190a1ef-8ddd-47c5-ae99-04c574601e31",
                "card_type": "employee",
                "status": "active",
                "valid_from": "2024-01-01T00:00:00",
                "valid_until": "2024-12-31T23:59:59",
                "last_used": "2024-06-01T10:30:00",
                "use_count": 42,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-06-01T10:30:00"
            }
        }

class CardListResponse(BaseModel):
    """Response model for card list"""
    cards: List[CardResponse] = Field(..., description="List of cards")
    total: int = Field(..., description="Total number of cards", example=100)
    skip: int = Field(..., description="Number of cards skipped", example=0)
    limit: int = Field(..., description="Maximum number of cards returned", example=50)

    class Config:
        schema_extra = {
            "example": {
                "cards": [
                    {
                        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "card_id": "CARD001234",
                        "user_id": "f190a1ef-8ddd-47c5-ae99-04c574601e31",
                        "card_type": "employee",
                        "status": "active",
                        "valid_from": "2024-01-01T00:00:00",
                        "valid_until": "2024-12-31T23:59:59",
                        "last_used": "2024-06-01T10:30:00",
                        "use_count": 42,
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-06-01T10:30:00"
                    }
                ],
                "total": 100,
                "skip": 0,
                "limit": 50
            }
        }