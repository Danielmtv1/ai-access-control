"""
Access validation API endpoints.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import JSONResponse

from app.application.use_cases.access_use_cases import ValidateAccessUseCase
from app.api.schemas.access_schemas import AccessValidationRequest, AccessValidationResponse
from app.api.error_handlers import map_domain_error_to_http
from app.ports.card_repository_port import CardRepositoryPort
from app.ports.door_repository_port import DoorRepositoryPort
from app.ports.permission_repository_port import PermissionRepositoryPort
from app.ports.user_repository_port import UserRepositoryPort
from app.domain.services.mqtt_message_service import MqttMessageService
from app.api.dependencies.repository_dependencies import (
    get_card_repository, get_door_repository, get_user_repository, 
    get_permission_repository, get_mqtt_message_service
)
from app.domain.exceptions import (
    EntityNotFoundError,
    InvalidCardError,
    InvalidDoorError,
    AccessDeniedError
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/access",
    tags=["Access Control"],
    responses={
        400: {"description": "Bad Request - Invalid request data"},
        404: {"description": "Not Found - Card or door not found"},
        403: {"description": "Forbidden - Access denied"},
        422: {"description": "Validation Error - Invalid request format"},
        500: {"description": "Internal Server Error"}
    }
)




@router.post(
    "/validate",
    response_model=AccessValidationResponse,
    summary="Validate Access Request",
    description="""
    Validate if a card has access to a specific door in real-time.
    
    This endpoint is designed for IoT devices to validate access requests.
    It performs comprehensive validation including:
    
    - Card existence and activation status
    - Door accessibility and status
    - User permissions and schedules
    - PIN requirements for high-security doors
    - Master card privileges
    - Failed attempt lockouts
    
    Returns detailed access decision with reasoning for logging and device response.
    """,
    responses={
        200: {
            "description": "Access validation completed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "access_granted": {
                            "summary": "Access Granted",
                            "value": {
                                "access_granted": True,
                                "reason": "Access granted for John Doe",
                                "door_name": "Main Entrance",
                                "user_name": "John Doe",
                                "card_type": "employee",
                                "requires_pin": False,
                                "valid_until": "18:00",
                                "timestamp": "2024-01-15T09:00:00Z"
                            }
                        },
                        "access_denied": {
                            "summary": "Access Denied",
                            "value": {
                                "access_granted": False,
                                "reason": "Access outside permitted schedule",
                                "door_name": "Server Room",
                                "user_name": "Jane Smith",
                                "card_type": "employee",
                                "requires_pin": True,
                                "valid_until": None,
                                "timestamp": "2024-01-15T22:00:00Z"
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Card or door not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Card ABC123 not found"
                    }
                }
            }
        },
        403: {
            "description": "Access denied",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User John Doe does not have permission to access Server Room"
                    }
                }
            }
        }
    }
)
async def validate_access(
    validation_request: AccessValidationRequest = Body(
        ...,
        description="Access validation request with card ID, door ID, and optional PIN"
    ),
    card_repository: CardRepositoryPort = Depends(get_card_repository),
    door_repository: DoorRepositoryPort = Depends(get_door_repository),
    permission_repository = Depends(get_permission_repository),
    user_repository: UserRepositoryPort = Depends(get_user_repository),
    mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)
) -> AccessValidationResponse:
    """
    Validates whether a card is authorized to access a specified door at the current time.
    
    This endpoint processes real-time access validation requests from IoT devices, applying all relevant business rules such as card and door validity, user permissions, schedules, PIN requirements, and lockout status. Returns a detailed response indicating whether access is granted, along with contextual information including the reason, door and user names, card type, PIN requirement, validity period, and timestamp.
    """
    try:
        logger.info(f"Access validation request received: {validation_request.model_dump()}")
        
        # Create use case and execute validation
        validate_use_case = ValidateAccessUseCase(
            card_repository=card_repository,
            door_repository=door_repository,
            permission_repository=permission_repository,
            user_repository=user_repository,
            mqtt_service=mqtt_service,
            device_communication_service=None  # No device communication in this endpoint
        )
        
        result = await validate_use_case.execute(
            card_id=validation_request.card_id,
            door_id=validation_request.door_id,
            pin=validation_request.pin,
            device_id=validation_request.device_id
        )
        
        # Convert result to response
        response = AccessValidationResponse(
            access_granted=result.access_granted,
            reason=result.reason,
            door_name=result.door_name,
            user_name=result.user_name,
            card_type=result.card_type,
            requires_pin=result.requires_pin,
            valid_until=result.valid_until,
            timestamp=datetime.now(timezone.utc)
        )
        
        logger.info(f"Access validation response: granted={result.access_granted}")
        return response
        
    except EntityNotFoundError as e:
        logger.warning(f"Entity not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except (InvalidCardError, InvalidDoorError) as e:
        logger.warning(f"Invalid card/door: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except AccessDeniedError as e:
        logger.warning(f"Access denied: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in access validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during access validation"
        )