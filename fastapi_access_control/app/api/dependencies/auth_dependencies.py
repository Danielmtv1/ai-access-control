from fastapi import Depends, HTTPException, status,Request
from fastapi.security import OAuth2PasswordBearer
from app.domain.entities.user import User
from app.infrastructure.persistence.adapters.user_repository import SqlAlchemyUserRepository
from app.domain.services.auth_service import AuthService
from app.shared.database import AsyncSessionLocal
from uuid import UUID

from app.infrastructure.mqtt.adapters.asyncio_mqtt_adapter import AiomqttAdapter
from app.domain.services.mqtt_message_service import MqttMessageService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from JWT token"""
    try:
        auth_service = AuthService()
        user_repository = SqlAlchemyUserRepository(session_factory=AsyncSessionLocal)
        
        # Decode and validate token
        payload = auth_service.decode_token(token)
        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = UUID(payload["sub"])
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = await user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user 

def get_mqtt_adapter(request: Request) -> AiomqttAdapter:
    """Get MQTT adapter from application state"""
    return request.app.state.mqtt_adapter

def get_mqtt_message_service(request: Request) -> MqttMessageService:
    """Get MQTT message service from application state"""
    return request.app.state.mqtt_message_service