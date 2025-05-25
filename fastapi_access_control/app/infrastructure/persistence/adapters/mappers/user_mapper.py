from datetime import datetime
from app.domain.entities.user import User, Role, UserStatus
from app.infrastructure.database.models.user import UserModel

class UserMapper:
    """Mapeador entre entidades de dominio y modelos de base de datos"""
    
    @staticmethod
    def to_domain(model: UserModel) -> User:
        """Convierte un modelo de base de datos a una entidad de dominio"""
        if not model:
            return None
            
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            roles=[Role(role) for role in model.roles],
            status=UserStatus.ACTIVE if model.is_active else UserStatus.INACTIVE,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    @staticmethod
    def to_model(user: User) -> UserModel:
        """Convierte una entidad de dominio a un modelo de base de datos"""
        return UserModel(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            roles=[role.value for role in user.roles],
            is_active=user.status == UserStatus.ACTIVE,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    @staticmethod
    def update_model_from_domain(model: UserModel, user: User) -> UserModel:
        """Actualiza un modelo de base de datos con los datos de una entidad de dominio"""
        model.email = user.email
        model.hashed_password = user.hashed_password
        model.full_name = user.full_name
        model.roles = [role.value for role in user.roles]
        model.is_active = user.status == UserStatus.ACTIVE
        model.updated_at = datetime.utcnow()
        return model 