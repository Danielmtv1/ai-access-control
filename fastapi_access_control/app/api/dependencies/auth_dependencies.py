from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.domain.entities.user import User
from app.infrastructure.persistence.adapters.user_repository import SqlAlchemyUserRepository
from app.domain.services.auth_service import AuthService
from app.shared.database import AsyncSessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from JWT token"""
    try:
        auth_service = AuthService()
        user_repository = SqlAlchemyUserRepository(session_factory=AsyncSessionLocal)
        
        # Decode and validate token
        user_id = auth_service.decode_token(token)
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