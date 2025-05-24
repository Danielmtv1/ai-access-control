from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class UserClaims:
    """JWT Claims as value object"""
    user_id: int
    email: str
    roles: List[str]
    full_name: str
    
    def has_role(self, role: str) -> bool:
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        return any(role in self.roles for role in roles)

@dataclass(frozen=True)
class TokenPair:
    """Access and refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes 