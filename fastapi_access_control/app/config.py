from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Configuración de la base de datos
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/access_control"
    
    # Configuración MQTT
    MQTT_HOST: str = "mqtt"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    USE_TLS: bool = False
    
    # Configuración de seguridad
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configuración de la aplicación
    APP_NAME: str = "Sistema de Control de Acceso"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_prefix = ""

@lru_cache()
def get_settings() -> Settings:
    return Settings() 