import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from ..entities.user import User, Role
from ..value_objects.auth import UserClaims, TokenPair
from ...config import get_settings

class AuthService:
    """Domain service for authentication business logic"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    
    def generate_access_token(self, user: User) -> str:
        """Generate JWT access token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "roles": [role.value for role in user.roles],
            "iat": now,
            "exp": now + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "type": "access"
        }
        
        return jwt.encode(
            payload, 
            self.settings.SECRET_KEY, 
            algorithm=self.settings.ALGORITHM
        )
    
    def generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "iat": now,
            "exp": now + timedelta(days=7),  # 7 days
            "type": "refresh"
        }
        
        return jwt.encode(
            payload, 
            self.settings.SECRET_KEY, 
            algorithm=self.settings.ALGORITHM
        )
    
    def generate_token_pair(self, user: User) -> TokenPair:
        """Generate both access and refresh tokens"""
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.settings.SECRET_KEY, 
                algorithms=[self.settings.ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def extract_user_claims(self, token: str) -> Optional[UserClaims]:
        """Extract user claims from access token"""
        payload = self.decode_token(token)
        
        if not payload or payload.get("type") != "access":
            return None
        
        try:
            return UserClaims(
                user_id=UUID(payload["sub"]),
                email=payload["email"],
                full_name=payload["full_name"],
                roles=payload["roles"]
            )
        except (KeyError, ValueError):
            return None 