from typing import List
from ....domain.entities.user import User, Role, UserStatus
from ..user_model import UserModel

class UserMapper:
    """Mapper between domain User and UserModel"""
    
    @staticmethod
    def to_domain(user_model: UserModel) -> User:
        """Convert UserModel to domain User entity"""
        return User(
            id=user_model.id,
            email=user_model.email,
            hashed_password=user_model.hashed_password,
            full_name=user_model.full_name,
            roles=[Role(role) for role in user_model.roles],
            status=user_model.status,
            created_at=user_model.created_at,
            last_login=user_model.last_login
        )
    
    @staticmethod
    def to_model(user: User) -> UserModel:
        """Convert domain User entity to UserModel"""
        return UserModel(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            roles=[role.value for role in user.roles],
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    @staticmethod
    def update_model_from_domain(user_model: UserModel, user: User) -> UserModel:
        """Update existing UserModel with domain User data"""
        user_model.email = user.email
        user_model.hashed_password = user.hashed_password
        user_model.full_name = user.full_name
        user_model.roles = [role.value for role in user.roles]
        user_model.status = user.status
        user_model.last_login = user.last_login
        return user_model 