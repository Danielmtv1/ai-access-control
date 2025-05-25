from fastapi import APIRouter, HTTPException, Request, Depends
import logging
from datetime import datetime
from typing import List
from app.domain.services.mqtt_message_service import MqttMessageService
from app.api.dependencies.auth_dependencies import get_current_user
from app.api.schemas.mqtt_schemas import MqttMessageSchema

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get the MqttMessageService
def get_mqtt_message_service(request: Request) -> MqttMessageService:
    return request.app.state.mqtt_message_service

@router.get("/mqtt/messages", response_model=list[MqttMessageSchema])
async def get_mqtt_messages(mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)):
    try:
        messages = await mqtt_service.get_all_messages()
        return messages
    except Exception as e:
        logger.error(f"Error retrieving MQTT messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving messages")
