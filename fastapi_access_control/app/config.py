from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pydantic import ConfigDict, Field, field_validator, ValidationError
import logging
from urllib.parse import urlparse
import re
import secrets
import os
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Environment type for the application"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Environment configuration
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment (development, testing, production)"
    )
    
    # Database configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/postgres",
        description="Database connection URL"
    )
    
    # MQTT configuration
    MQTT_HOST: str = Field(
        default="mqtt",
        description="MQTT broker host"
    )
    MQTT_PORT: int = Field(
        default=1883,
        ge=1,
        le=65535,
        description="MQTT broker port"
    )
    MQTT_WS_PORT: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
        description="MQTT WebSocket port"
    )
    MQTT_USERNAME: Optional[str] = Field(
        default=None,
        min_length=1,
        description="MQTT broker username"
    )
    MQTT_PASSWORD: Optional[str] = Field(
        default=None,
        min_length=1,
        description="MQTT broker password"
    )
    USE_TLS: bool = Field(
        default=False,
        description="Use TLS for MQTT connection"
    )
    MQTT_KEEPALIVE: int = Field(
        default=60,
        ge=5,
        le=3600,
        description="MQTT keepalive in seconds"
    )
    MQTT_CLEAN_SESSION: bool = Field(
        default=True,
        description="Use clean session for MQTT"
    )
    MQTT_QOS: int = Field(
        default=1,
        ge=0,
        le=2,
        description="MQTT Quality of Service level"
    )
    MQTT_MAX_QUEUED_MESSAGES: int = Field(
        default=0,
        ge=0,
        description="Maximum queued MQTT messages (0 = unlimited)"
    )
    
    # General configuration
    DEBUG: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    # Authentication configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiration in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiration in days"
    )
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: f"dev_{secrets.token_urlsafe(32)}" if os.getenv("ENVIRONMENT") == "development" else None,
        min_length=32,
        description="Secret key for JWT tokens"
    )
    SECRET_KEY: str = Field(
        default_factory=lambda: f"dev_{secrets.token_urlsafe(32)}" if os.getenv("ENVIRONMENT") == "development" else None,
        min_length=32,
        description="Application secret key"
    )
    ALGORITHM: str = Field(
        default="HS256",
        pattern="^(HS256|HS384|HS512|RS256|RS384|RS512)$",
        description="JWT signing algorithm"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        validate_default=True
    )
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid database URL format")
            if not result.scheme.startswith('postgresql'):
                raise ValueError("Only PostgreSQL database is supported")
            return v
        except Exception as e:
            raise ValueError(f"Invalid database URL: {str(e)}")
    
    @field_validator('MQTT_HOST')
    @classmethod
    def validate_mqtt_host(cls, v: str) -> str:
        """Validate MQTT host format"""
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError("Invalid MQTT host format")
        return v
    
    @field_validator('MQTT_USERNAME', 'MQTT_PASSWORD')
    @classmethod
    def validate_mqtt_credentials(cls, v: Optional[str], info) -> Optional[str]:
        """Validate MQTT credentials"""
        if info.field_name == 'MQTT_USERNAME' and v is not None:
            if not re.match(r'^[a-zA-Z0-9._-]+$', v):
                raise ValueError("Invalid MQTT username format")
        return v
    
    @field_validator('JWT_SECRET_KEY', 'SECRET_KEY')
    @classmethod
    def validate_secret_keys(cls, v: str, info) -> str:
        """Validate secret keys based on environment"""
        if not v:
            raise ValueError(f"{info.field_name} is required")
        
        if v.startswith('dev_') and os.getenv("ENVIRONMENT") == "production":
            raise ValueError(f"Development {info.field_name} not allowed in production")
        
        if not v.startswith('dev_') and os.getenv("ENVIRONMENT") == "development":
            logger.warning(f"Production {info.field_name} used in development environment")
        
        return v
    
    def validate_security_settings(self) -> None:
        """Validate security-related settings"""
        if self.ENVIRONMENT == Environment.DEVELOPMENT:
            if not self.SECRET_KEY.startswith('dev_'):
                logger.warning("Running in development with production secret key")
            if not self.JWT_SECRET_KEY.startswith('dev_'):
                logger.warning("Running in development with production JWT secret key")
        else:
            if self.SECRET_KEY.startswith('dev_'):
                raise ValueError("Development secret key not allowed in production")
            if self.JWT_SECRET_KEY.startswith('dev_'):
                raise ValueError("Development JWT secret key not allowed in production")
        
        if self.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
            logger.warning("Access token expiration time is longer than recommended")
        
        if self.REFRESH_TOKEN_EXPIRE_DAYS > 7:
            logger.warning("Refresh token expiration time is longer than recommended")
        
        if self.ENVIRONMENT == Environment.PRODUCTION and self.DEBUG:
            raise ValueError("Debug mode not allowed in production")

def validate_settings() -> Settings:
    """Validate all settings and return validated settings instance"""
    try:
        settings = Settings()
        settings.validate_security_settings()
        logger.info(f"Configuration validated successfully for {settings.ENVIRONMENT.value} environment")
        return settings
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during configuration validation: {str(e)}")
        raise

@lru_cache()
def get_settings() -> Settings:
    """Get validated settings instance"""
    return validate_settings() 