from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MqttMessage:
    """Entidad de dominio para mensajes MQTT - Sin dependencias externas"""
    id: Optional[int]
    topic: str
    message: str
    timestamp: datetime
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()
    
    def is_valid(self) -> bool:
        """Lógica de dominio pura"""
        return bool(self.topic and self.message)
    
    def is_system_message(self) -> bool:
        """Determina si es un mensaje del sistema"""
        return self.topic.startswith("system/") 