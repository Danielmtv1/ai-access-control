from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # Configuración de la base de datos
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/postgres"
    
    # Configuración MQTT
    MQTT_HOST: str = "mqtt"
    MQTT_PORT: int = 1883
    MQTT_WS_PORT: Optional[int] = None
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    USE_TLS: bool = False
    
    # Configuración de seguridad
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configuración de la aplicación
    APP_NAME: str = "Sistema de Control de Acceso"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings() 