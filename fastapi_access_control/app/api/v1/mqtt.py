from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.schemas.mqtt_schemas import (
    MqttMessageCreate,
    MqttMessageResponse,
    MqttMessageList
)
from app.domain.entities.mqtt_message import MqttMessage
from app.domain.services.mqtt_message_service import MqttMessageService
from app.api.dependencies import get_mqtt_service

router = APIRouter(prefix="/mqtt", tags=["MQTT"])

@router.post("/messages", response_model=MqttMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MqttMessageCreate,
    mqtt_service: MqttMessageService = Depends(get_mqtt_service)
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

@router.get("/messages", response_model=MqttMessageList)
async def get_messages(
    mqtt_service: MqttMessageService = Depends(get_mqtt_service)
) -> MqttMessageList:
    """Get all MQTT messages"""
    messages = await mqtt_service.get_all_messages()
    
    return MqttMessageList(
        messages=[
            MqttMessageResponse(
                id=msg.id,
                topic=msg.topic,
                message=msg.message,
                timestamp=msg.timestamp
            )
            for msg in messages
        ],
        total=len(messages)
    )

@router.get("/messages/{message_id}", response_model=MqttMessageResponse)
async def get_message(
    message_id: int,
    mqtt_service: MqttMessageService = Depends(get_mqtt_service)
) -> MqttMessageResponse:
    """Get MQTT message by ID"""
    message = await mqtt_service.get_message_by_id(message_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return MqttMessageResponse(
        id=message.id,
        topic=message.topic,
        message=message.message,
        timestamp=message.timestamp
    )

@router.get("/messages/topic/{topic}", response_model=MqttMessageList)
async def get_messages_by_topic(
    topic: str,
    mqtt_service: MqttMessageService = Depends(get_mqtt_service)
) -> MqttMessageList:
    """Get MQTT messages by topic"""
    messages = await mqtt_service.get_messages_by_topic(topic)
    
    return MqttMessageList(
        messages=[
            MqttMessageResponse(
                id=msg.id,
                topic=msg.topic,
                message=msg.message,
                timestamp=msg.timestamp
            )
            for msg in messages
        ],
        total=len(messages)
    ) 