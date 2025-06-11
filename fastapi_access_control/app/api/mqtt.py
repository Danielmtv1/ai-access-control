import logging  # ← Correcto
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID  # ← Añadir para UUID

from app.api.schemas.mqtt_schemas import (
    MqttMessageCreate,
    MqttMessageResponse,
    MqttMessageList
)
from app.domain.entities.mqtt_message import MqttMessage
from app.domain.services.mqtt_message_service import MqttMessageService
from app.infrastructure.mqtt.adapters.asyncio_mqtt_adapter import AiomqttAdapter
from app.api.dependencies.auth_dependencies import get_mqtt_adapter, get_mqtt_message_service  # ← Correcto path

logger = logging.getLogger(__name__)  # ← Crear logger correcto
router = APIRouter(prefix="/mqtt", tags=["MQTT"])

@router.post("/messages", response_model=MqttMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MqttMessageCreate,
    mqtt_service: MqttMessageService = Depends(get_mqtt_message_service),
    mqtt_adapter: AiomqttAdapter = Depends(get_mqtt_adapter)
) -> MqttMessageResponse:
    """Create a new MQTT message"""
    try:
        logger.info(f"Creating message with topic='{message_data.topic}', message='{message_data.message}'")
        
        # Convert API schema to domain entity
        domain_message = MqttMessage.create(
            topic=message_data.topic,
            message=message_data.message
        )
        
        logger.info(f"Domain message created: {domain_message}")
        
        # Use domain service to save message
        saved_message = await mqtt_service.save_message(domain_message)
        logger.info(f"Message saved to DB: {saved_message.id}")
        
        # Enviar mensaje al broker MQTT
        logger.info(f"About to publish to MQTT: topic='{saved_message.topic}', message='{saved_message.message}'")
        
        await mqtt_adapter.publish(
            topic=saved_message.topic,
            payload=saved_message.message
        )
        
        logger.info(f"Message published to MQTT topic: {saved_message.topic}")
        
        # Convert domain entity to API response
        return MqttMessageResponse(
            id=saved_message.id,
            topic=saved_message.topic,
            message=saved_message.message,
            timestamp=saved_message.timestamp
        )
    except ValueError as e:
        logger.error(f"ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Exception publishing MQTT message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish message to MQTT broker"
        )

@router.get("/messages", response_model=MqttMessageList)
async def get_messages(
    mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)  # ← Corregido
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
    message_id: UUID,  # ← Cambiado de int a UUID
    mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)  # ← Corregido
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
    mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)  # ← Corregido
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