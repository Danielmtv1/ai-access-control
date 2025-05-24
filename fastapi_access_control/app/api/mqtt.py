from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import logging
from ..domain.mqtt_message import MqttMessage # Keep import for schema definition
from datetime import datetime
from ..domain.services import MqttMessageService # Import the domain service
from fastapi import Depends # Keep Depends import

logger = logging.getLogger(__name__)

router = APIRouter()

class MqttMessageSchema(BaseModel):
    id: int
    topic: str
    message: str
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

# Dependency to get the MqttMessageService
def get_mqtt_message_service(request: Request) -> MqttMessageService:
    return request.app.state.mqtt_message_service

@router.get("/mqtt/messages", response_model=list[MqttMessageSchema]) # Specify response model
async def get_mqtt_messages(mqtt_service: MqttMessageService = Depends(get_mqtt_message_service)): # Inject Domain Service
    # Use the domain service to get messages
    try:
        messages = await mqtt_service.get_all_messages()
        return messages
    except Exception as e:
        logger.error(f"Error retrieving MQTT messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error retrieving messages")
