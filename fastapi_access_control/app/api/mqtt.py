from fastapi import APIRouter, HTTPException, Request, Depends, status
import logging
from datetime import datetime
from typing import List
from app.domain.services.mqtt_message_service import MqttMessageService
from app.api.dependencies.auth_dependencies import get_current_user
from app.api.schemas.mqtt_schemas import (
    MqttMessageCreate,
    MqttMessageResponse,
    MqttMessageList
)
from app.domain.entities.mqtt_message import MqttMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mqtt", tags=["MQTT"])

# Dependency to get the MqttMessageService
def get_mqtt_message_service(request: Request) -> MqttMessageService:
    return request.app.state.mqtt_message_service

@router.get("/messages", response_model=MqttMessageList)
async def get_mqtt_messages(mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)):
    try:
        messages = await mqtt_service.get_all_messages()
        return MqttMessageList(
            messages=[
                MqttMessageResponse(
                    id=msg.id,
                    topic=msg.topic,
                    message=msg.message,
                    timestamp=msg.timestamp
                ) for msg in messages
            ],
            total=len(messages)
        )
    except Exception as e:
        logger.error(f"Error retrieving MQTT messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving messages")

@router.post("/messages", response_model=MqttMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MqttMessageCreate,
    mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)
) -> MqttMessageResponse:
    """Create a new MQTT message"""
    try:
        # Convert API schema to domain entity
        domain_message = MqttMessage.create(
            topic=message_data.topic,
            message=message_data.message
        )
        
        # Use domain service to save message
        saved_message = await mqtt_service.save_message(domain_message)
        
        # Convert domain entity to API response
        return MqttMessageResponse(
            id=saved_message.id,
            topic=saved_message.topic,
            message=saved_message.message,
            timestamp=saved_message.timestamp
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
