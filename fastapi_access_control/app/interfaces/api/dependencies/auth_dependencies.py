from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from app.domain.services.auth_service import AuthService
from app.domain.value_objects.auth import UserClaims
from app.domain.entities.user import Role
from app.ports.user_repository_port import UserRepositoryPort
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from app.shared.database import AsyncSessionLocal

# Security scheme
security = HTTPBearer()

def get_auth_service() -> AuthService:
    """Dependency to get AuthService"""
    return AuthService()

def get_user_repository() -> UserRepositoryPort:
    """Dependency to get UserRepository"""
    def db_session_factory():
        return AsyncSessionLocal()
    return SqlAlchemyUserRepository(session_factory=db_session_factory)

async def get_current_user_claims(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserClaims:
    """Extract current user claims from JWT token"""
    token = credentials.credentials
    
    user_claims = auth_service.extract_user_claims(token)
    
    if not user_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_claims

async def get_current_user(
    claims: UserClaims = Depends(get_current_user_claims),
    user_repository: UserRepositoryPort = Depends(get_user_repository)
):
    """Get current user entity from claims"""
    user = await user_repository.get_by_id(claims.user_id)
    
    if not user or not user.is_active():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

def require_roles(required_roles: List[Role]):
    """Dependency factory for role-based access control"""
    def role_checker(claims: UserClaims = Depends(get_current_user_claims)):
        user_roles = [Role(role) for role in claims.roles]
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return claims
    
    return role_checker

# Convenience dependencies for common role checks
require_admin = require_roles([Role.ADMIN])
require_operator = require_roles([Role.ADMIN, Role.OPERATOR])
require_viewer = require_roles([Role.ADMIN, Role.OPERATOR, Role.VIEWER]) 