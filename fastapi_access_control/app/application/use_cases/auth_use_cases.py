from typing import Optional
from ...domain.entities.user import User, Role, UserStatus
from ...domain.services.auth_service import AuthService
from ...domain.value_objects.auth import TokenPair, UserClaims
from ...ports.user_repository_port import UserRepositoryPort
from ...domain.exceptions import DomainError, UserNotFoundError, EntityAlreadyExistsError
from datetime import datetime, timezone, UTC
from uuid import UUID
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class AuthenticationError(DomainError):
    """Authentication specific error"""
    pass

class AuthenticateUserUseCase:
    """Use case for user authentication"""
    
    def __init__(self, 
                 auth_service: AuthService,
                 user_repository: UserRepositoryPort):
        self.auth_service = auth_service
        self.user_repository = user_repository
    
    async def execute(self, email: str, password: str) -> TokenPair:
        """
        Authenticates a user by email and password and returns a token pair.
        
        Raises:
            AuthenticationError: If the user does not exist, the password is incorrect, or the user account is inactive.
        
        Returns:
            TokenPair: An object containing access and refresh tokens for the authenticated user.
        """
        logger.info(f"Buscando usuario con email: {email}")
        # Get user by email
        user = await self.user_repository.get_by_email(email)
        
        if not user:
            logger.error(f"Usuario no encontrado: {email}")
            raise AuthenticationError("Invalid email or password")
        
        logger.info(f"Usuario encontrado: {email}")
        # Verify password
        if not self.auth_service.verify_password(password, user.hashed_password):
            logger.error(f"Contraseña incorrecta para usuario: {email}")
            raise AuthenticationError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active():
            logger.error(f"Usuario inactivo: {email}")
            raise AuthenticationError("User account is not active")
        
        logger.info(f"Autenticación exitosa para usuario: {email}")
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.user_repository.update(user)
        
        # Generate tokens
        return self.auth_service.generate_token_pair(user)

class RefreshTokenUseCase:
    """Use case for refreshing access token"""
    
    def __init__(self, 
                 user_repository: UserRepositoryPort, 
                 auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self, refresh_token: str) -> TokenPair:
        """Refresh access token using refresh token"""
        payload = self.auth_service.decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")
        
        # Get user
        user_id = UUID(payload["sub"])
        user = await self.user_repository.get_by_id(user_id)
        
        if not user or not user.is_active():
            raise AuthenticationError("User not found or inactive")
        
        # Generate new token pair
        return self.auth_service.generate_token_pair(user)

class CreateUserUseCase:
    """Use case for creating new users"""
    
    def __init__(self, 
                 user_repository: UserRepositoryPort, 
                 auth_service: AuthService):
        self.user_repository = user_repository
        self.auth_service = auth_service
    
    async def execute(self, 
                     email: str, 
                     password: str, 
                     full_name: str,
                     roles: list[str] = None) -> User:
        """
                     Creates a new user account with the specified email, password, full name, and roles.
                     
                     If a user with the given email already exists, raises an EntityAlreadyExistsError. The password is securely hashed before storage. If no roles are provided, the user is assigned the default USER role. The new user is created with active status and current UTC timestamps.
                     
                     Args:
                         email: The user's email address.
                         password: The user's plaintext password.
                         full_name: The user's full name.
                         roles: Optional list of role names to assign to the user.
                     
                     Returns:
                         The created User entity.
                     """
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise EntityAlreadyExistsError("User", email)
        
        # Hash password
        hashed_password = self.auth_service.hash_password(password)
        
        # Set default roles if none provided
        if not roles:
            roles = [Role.USER]
        else:
            roles = [Role(role) for role in roles]
        
        # Create user entity
        now = datetime.now(UTC).replace(tzinfo=None)
        user = User(
            id=None,  # Will be set by database
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            roles=roles,
            status=UserStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        
        return await self.user_repository.create(user) 