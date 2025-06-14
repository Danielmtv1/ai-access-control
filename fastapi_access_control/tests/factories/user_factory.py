"""
User factory for creating test user entities and database models.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.domain.entities.user import User, Role, UserStatus
from app.infrastructure.database.models.user import UserModel
from app.domain.services.auth_service import AuthService
from .base_factory import EntityFactory, DatabaseFactory


class UserFactory(EntityFactory):
    """Factory for creating User domain entities."""
    
    @classmethod
    def get_entity_class(cls):
        return User
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build user attributes with sensible defaults."""
        defaults = {
            'id': cls.generate_uuid('user'),
            'email': cls.generate_email('user'),
            'full_name': cls.generate_name('Test', 'User'),
            'roles': [Role.USER],
            'status': UserStatus.ACTIVE,
            'last_login': None,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> User:
        """Create a User entity."""
        return cls.create_entity(**kwargs)
    
    @classmethod
    def create_admin(cls, **kwargs) -> User:
        """Create an admin user."""
        admin_defaults = {
            'email': cls.generate_email('admin'),
            'full_name': cls.generate_name('Admin', 'User'),
            'roles': [Role.ADMIN]
        }
        return cls.create(**cls.merge_kwargs(admin_defaults, kwargs))
    
    @classmethod
    def create_operator(cls, **kwargs) -> User:
        """Create an operator user."""
        operator_defaults = {
            'email': cls.generate_email('operator'),
            'full_name': cls.generate_name('Operator', 'User'),
            'roles': [Role.OPERATOR]
        }
        return cls.create(**cls.merge_kwargs(operator_defaults, kwargs))
    
    @classmethod
    def create_viewer(cls, **kwargs) -> User:
        """Create a viewer user."""
        viewer_defaults = {
            'email': cls.generate_email('viewer'),
            'full_name': cls.generate_name('Viewer', 'User'),
            'roles': [Role.VIEWER]
        }
        return cls.create(**cls.merge_kwargs(viewer_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> User:
        """Create an inactive user."""
        inactive_defaults = {
            'status': UserStatus.INACTIVE,
            'email': cls.generate_email('inactive')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_suspended(cls, **kwargs) -> User:
        """Create a suspended user."""
        suspended_defaults = {
            'status': UserStatus.SUSPENDED,
            'email': cls.generate_email('suspended')
        }
        return cls.create(**cls.merge_kwargs(suspended_defaults, kwargs))
    
    @classmethod
    def create_with_multiple_roles(cls, roles: List[Role], **kwargs) -> User:
        """Create a user with multiple roles."""
        multi_role_defaults = {
            'roles': roles,
            'email': cls.generate_email('multirole')
        }
        return cls.create(**cls.merge_kwargs(multi_role_defaults, kwargs))


class UserModelFactory(DatabaseFactory):
    """Factory for creating UserModel database instances."""
    
    @classmethod
    def get_model_class(cls):
        return UserModel
    
    @classmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """Build user model attributes with sensible defaults."""
        defaults = {
            'id': cls.generate_uuid('user'),
            'email': cls.generate_email('user'),
            'hashed_password': cls._generate_hashed_password('password123'),
            'full_name': cls.generate_name('Test', 'User'),
            'roles': ['user'],
            'is_active': True,
            'last_login': None,
            'created_at': cls.current_utc_time(),
            'updated_at': cls.current_utc_time()
        }
        return cls.merge_kwargs(defaults, kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> UserModel:
        """Create a UserModel instance."""
        return cls.create_model(**kwargs)
    
    @classmethod
    def create_admin(cls, **kwargs) -> UserModel:
        """Create an admin user model."""
        admin_defaults = {
            'email': cls.generate_email('admin'),
            'full_name': cls.generate_name('Admin', 'User'),
            'roles': ['admin']
        }
        return cls.create(**cls.merge_kwargs(admin_defaults, kwargs))
    
    @classmethod
    def create_operator(cls, **kwargs) -> UserModel:
        """Create an operator user model."""
        operator_defaults = {
            'email': cls.generate_email('operator'),
            'full_name': cls.generate_name('Operator', 'User'),
            'roles': ['operator']
        }
        return cls.create(**cls.merge_kwargs(operator_defaults, kwargs))
    
    @classmethod
    def create_inactive(cls, **kwargs) -> UserModel:
        """Create an inactive user model."""
        inactive_defaults = {
            'is_active': False,
            'email': cls.generate_email('inactive')
        }
        return cls.create(**cls.merge_kwargs(inactive_defaults, kwargs))
    
    @classmethod
    def create_with_specific_id(cls, user_id: UUID, **kwargs) -> UserModel:
        """Create user model with specific ID (useful for testing relationships)."""
        specific_defaults = {'id': user_id}
        return cls.create(**cls.merge_kwargs(specific_defaults, kwargs))
    
    @classmethod
    def _generate_hashed_password(cls, plain_password: str = 'password123') -> str:
        """Generate a hashed password for testing."""
        auth_service = AuthService()
        return auth_service.hash_password(plain_password)


# Convenience aliases for backward compatibility
create_test_user = UserFactory.create
create_admin_user = UserFactory.create_admin
create_test_user_model = UserModelFactory.create
create_admin_user_model = UserModelFactory.create_admin