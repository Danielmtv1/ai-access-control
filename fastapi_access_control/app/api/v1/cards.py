from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List
from uuid import UUID
from app.domain.entities.card import Card
from app.application.use_cases.card_use_cases import (
    CreateCardUseCase, GetCardUseCase, GetCardByCardIdUseCase, GetUserCardsUseCase,
    UpdateCardUseCase, DeactivateCardUseCase, SuspendCardUseCase, ListCardsUseCase, DeleteCardUseCase
)
from app.api.schemas.card_schemas import (
    CreateCardRequest, UpdateCardRequest, CardResponse, CardListResponse
)
from app.api.error_handlers import map_domain_error_to_http
from app.api.dependencies.auth_dependencies import get_current_active_user
from app.api.dependencies.repository_dependencies import get_card_repository, get_user_repository
from app.ports.card_repository_port import CardRepositoryPort
from app.ports.user_repository_port import UserRepositoryPort
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cards",
    tags=["Cards"],
    dependencies=[Depends(get_current_active_user)],
    responses={
        401: {"description": "Unauthorized - Invalid or missing token"},
        403: {"description": "Forbidden - Insufficient permissions"},
        422: {"description": "Validation Error - Invalid request data"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post(
    "/",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Card",
    description="""
    Create a new access card for a user.
    
    This endpoint creates a new access card with the specified details.
    The card will be associated with the specified user and can be used for access control.
    """,
    responses={
        201: {
            "description": "Card created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                        "card_id": "CARD001234",
                        "user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d478",
                        "card_type": "employee",
                        "status": "active",
                        "valid_from": "2024-01-01T00:00:00",
                        "valid_until": "2024-12-31T23:59:59",
                        "last_used": None,
                        "use_count": 0,
                        "created_at": "2024-06-08T21:52:00",
                        "updated_at": "2024-06-08T21:52:00"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid input data"
        },
        404: {
            "description": "Not Found - User not found"
        },
        409: {
            "description": "Conflict - Card ID already exists"
        }
    }
)
async def create_card(
    card_data: CreateCardRequest = Body(..., description="Card creation data"),
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    current_user = Depends(get_current_active_user)
):
    """Create a new access card"""
    try:
        logger.info(f"Creating card {card_data.card_id} for user {card_data.user_id}")
        
        create_card_use_case = CreateCardUseCase(card_repository, user_repository)
        card = await create_card_use_case.execute(
            card_id=card_data.card_id,
            user_id=card_data.user_id,
            card_type=card_data.card_type.value,
            valid_from=card_data.valid_from,
            valid_until=card_data.valid_until
        )
        
        logger.info(f"Card {card.card_id} created successfully with ID {card.id}")
        return CardResponse.from_entity(card)
        
    except Exception as e:
        logger.error(f"Error creating card: {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/{card_id}",
    response_model=CardResponse,
    summary="Get Card by ID",
    description="Retrieve a card by its database ID",
    responses={
        404: {"description": "Card not found"}
    }
)
async def get_card(
    card_id: UUID,
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """Get a card by its database ID"""
    try:
        get_card_use_case = GetCardUseCase(card_repository)
        card = await get_card_use_case.execute(card_id)
        return CardResponse.model_validate(card, from_attributes=True) 
    except Exception as e:
        logger.error(f"Error getting card {card_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/by-card-id/{card_id}",
    response_model=CardResponse,
    summary="Get Card by Physical Card ID",
    description="Retrieve a card by its physical card identifier (RFID, NFC, etc.)",
    responses={
        404: {"description": "Card not found"}
    }
)
async def get_card_by_card_id(
    card_id: str,
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """Get a card by its physical card ID"""
    try:
        get_card_use_case = GetCardByCardIdUseCase(card_repository)
        card = await get_card_use_case.execute(card_id)
        return CardResponse.model_validate(card, from_attributes=True)
    except Exception as e:
        logger.error(f"Error getting card by card_id {card_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/user/{user_id}",
    response_model=List[CardResponse],
    summary="Get User Cards",
    description="Retrieve all cards for a specific user",
)
async def get_user_cards(
    user_id: UUID,
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """Get all cards for a user"""
    try:
        get_user_cards_use_case = GetUserCardsUseCase(card_repository)
        cards = await get_user_cards_use_case.execute(user_id)
        return [CardResponse.model_validate(card, from_attributes=True) for card in cards]
    except Exception as e:
        logger.error(f"Error getting cards for user {user_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.get(
    "/",
    response_model=CardListResponse,
    summary="List Cards",
    description="List all cards with pagination"
)
async def list_cards(
    skip: int = Query(0, ge=0, description="Number of cards to skip"),
    limit: int = Query(get_settings().DEFAULT_PAGE_SIZE, ge=1, le=get_settings().MAX_PAGE_SIZE, description="Maximum number of cards to return"),
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """List cards with pagination"""
    try:
        list_cards_use_case = ListCardsUseCase(card_repository)
        cards = await list_cards_use_case.execute(skip, limit)
        
        # Get total count (simplified - in production, you'd want a separate count method)
        total = len(cards) + skip  # This is a simplified approach
        
        return CardListResponse(
            cards=[CardResponse.model_validate(card, from_attributes=True) for card in cards],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing cards: {str(e)}")
        raise map_domain_error_to_http(e)

@router.put(
    "/{card_id}",
    response_model=CardResponse,
    summary="Update Card",
    description="Update card information"
)
async def update_card(
    card_id: UUID,
    card_data: UpdateCardRequest = Body(..., description="Card update data"),
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """Update a card"""
    try:
        logger.info(f"Updating card {card_id}")
        
        update_card_use_case = UpdateCardUseCase(card_repository)
        card = await update_card_use_case.execute(
            card_id=card_id,
            card_type=card_data.card_type.value if card_data.card_type else None,
            status=card_data.status.value if card_data.status else None,
            valid_until=card_data.valid_until
        )
        
        logger.info(f"Card {card_id} updated successfully")
        return CardResponse.model_validate(card, from_attributes=True)
        
    except Exception as e:
        logger.error(f"Error updating card {card_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.post(
    "/{card_id}/deactivate",
    response_model=CardResponse,
    summary="Deactivate Card",
    description="Deactivate a card to prevent access"
)
async def deactivate_card(
    card_id: UUID,
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """Deactivate a card"""
    try:
        logger.info(f"Deactivating card {card_id}")
        
        deactivate_card_use_case = DeactivateCardUseCase(card_repository)
        card = await deactivate_card_use_case.execute(card_id)
        
        logger.info(f"Card {card_id} deactivated successfully")
        return CardResponse.model_validate(card, from_attributes=True)
        
    except Exception as e:
        logger.error(f"Error deactivating card {card_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.post(
    "/{card_id}/suspend",
    response_model=CardResponse,
    summary="Suspend Card",
    description="Suspend a card temporarily"
)
async def suspend_card(
    card_id: UUID,
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """Suspend a card"""
    try:
        logger.info(f"Suspending card {card_id}")
        
        suspend_card_use_case = SuspendCardUseCase(card_repository)
        card = await suspend_card_use_case.execute(card_id)
        
        logger.info(f"Card {card_id} suspended successfully")
        return CardResponse.model_validate(card, from_attributes=True)
        
    except Exception as e:
        logger.error(f"Error suspending card {card_id}: {str(e)}")
        raise map_domain_error_to_http(e)

@router.delete(
    "/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Card",
    description="Delete a card permanently"
)
async def delete_card(
    card_id: UUID,
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    current_user = Depends(get_current_active_user)
):
    """Delete a card"""
    try:
        logger.info(f"Deleting card {card_id}")
        
        delete_card_use_case = DeleteCardUseCase(card_repository)
        deleted = await delete_card_use_case.execute(card_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Card with ID {card_id} not found"
            )
        
        logger.info(f"Card {card_id} deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting card {card_id}: {str(e)}")
        raise map_domain_error_to_http(e)