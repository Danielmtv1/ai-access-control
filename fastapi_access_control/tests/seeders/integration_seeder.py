"""
Integration test database seeder with optimized performance and relationship management.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..factories import UserModelFactory, CardModelFactory, DoorModelFactory, PermissionModelFactory
from .base_seeder import BulkSeeder

logger = logging.getLogger(__name__)


class IntegrationSeeder(BulkSeeder):
    """Optimized seeder for integration tests with relationship management."""
    
    async def seed(self) -> Dict[str, Any]:
        """Default seed method - creates basic test data."""
        return await self.seed_basic_integration_data()
    
    async def seed_basic_integration_data(self) -> Dict[str, Any]:
        """Seed basic data for integration tests."""
        logger.info("Seeding basic integration test data")
        
        # Create users
        admin = await self._save_object(UserModelFactory.create_admin(
            email="integration_admin@test.com"
        ))
        
        user = await self._save_object(UserModelFactory.create(
            email="integration_user@test.com"
        ))
        
        # Create doors
        main_door = await self._save_object(DoorModelFactory.create(
            name="Integration Main Door"
        ))
        
        secure_door = await self._save_object(DoorModelFactory.create_high_security(
            name="Integration Secure Door"
        ))
        
        # Create cards
        admin_card = await self._save_object(CardModelFactory.create_master(
            user_id=admin.id
        ))
        
        user_card = await self._save_object(CardModelFactory.create(
            user_id=user.id
        ))
        
        # Create permissions
        admin_main_permission = await self._save_object(
            PermissionModelFactory.create_for_user_and_door(admin.id, main_door.id)
        )
        
        admin_secure_permission = await self._save_object(
            PermissionModelFactory.create_for_user_and_door(admin.id, secure_door.id)
        )
        
        user_main_permission = await self._save_object(
            PermissionModelFactory.create_for_user_and_door(user.id, main_door.id)
        )
        
        await self._commit_changes()
        
        return {
            'admin_user': admin,
            'regular_user': user,
            'main_door': main_door,
            'secure_door': secure_door,
            'admin_card': admin_card,
            'user_card': user_card,
            'admin_main_permission': admin_main_permission,
            'admin_secure_permission': admin_secure_permission,
            'user_main_permission': user_main_permission
        }
    
    async def seed_complete_access_flow_data(self) -> Dict[str, Any]:
        """Seed data specifically for complete access flow tests."""
        logger.info("Seeding complete access flow test data")
        
        # Create admin user
        admin = await self._save_object(UserModelFactory.create_admin(
            email="flow_admin@test.com",
            full_name="Flow Test Admin"
        ))
        
        # Create regular user
        user = await self._save_object(UserModelFactory.create(
            email="flow_user@test.com",
            full_name="Flow Test User"
        ))
        
        # Create test doors with different security levels
        low_security_door = await self._save_object(DoorModelFactory.create_low_security(
            name="Low Security Test Door",
            location="Test Building - Floor 1"
        ))
        
        medium_security_door = await self._save_object(DoorModelFactory.create(
            name="Medium Security Test Door",
            location="Test Building - Floor 2",
            security_level="MEDIUM"
        ))
        
        high_security_door = await self._save_object(DoorModelFactory.create_high_security(
            name="High Security Test Door",
            location="Test Building - Server Room"
        ))
        
        # Create cards
        admin_master_card = await self._save_object(CardModelFactory.create_master(
            user_id=admin.id,
            card_id="FLOW_ADMIN_MASTER"
        ))
        
        user_standard_card = await self._save_object(CardModelFactory.create(
            user_id=user.id,
            card_id="FLOW_USER_STANDARD"
        ))
        
        # Create comprehensive permissions
        permissions = []
        
        # Admin gets access to all doors
        for door in [low_security_door, medium_security_door, high_security_door]:
            permission = await self._save_object(
                PermissionModelFactory.create_for_user_and_door(admin.id, door.id)
            )
            permissions.append(permission)
        
        # Regular user gets access to low and medium security doors only
        for door in [low_security_door, medium_security_door]:
            permission = await self._save_object(
                PermissionModelFactory.create_for_user_and_door(user.id, door.id)
            )
            permissions.append(permission)
        
        await self._commit_changes()
        
        return {
            'admin_user': admin,
            'regular_user': user,
            'doors': {
                'low_security': low_security_door,
                'medium_security': medium_security_door,
                'high_security': high_security_door
            },
            'cards': {
                'admin_master': admin_master_card,
                'user_standard': user_standard_card
            },
            'permissions': permissions
        }
    
    async def seed_repository_test_data(self) -> Dict[str, Any]:
        """Seed data for repository integration tests."""
        logger.info("Seeding repository test data")
        
        # Create multiple users for testing pagination and filtering
        users = []
        for i in range(5):
            user = UserModelFactory.create(
                email=f"repo_test_user_{i}@test.com",
                full_name=f"Repository Test User {i}"
            )
            users.append(user)
        
        saved_users = await self.bulk_save_objects(users)
        
        # Create multiple doors
        doors = []
        security_levels = ["LOW", "MEDIUM", "HIGH"]
        for i in range(3):
            door = DoorModelFactory.create(
                name=f"Repository Test Door {i}",
                security_level=security_levels[i],
                location=f"Test Building - Area {i}"
            )
            doors.append(door)
        
        saved_doors = await self.bulk_save_objects(doors)
        
        # Create cards for each user
        cards = []
        for user in saved_users:
            card = CardModelFactory.create(user_id=user.id)
            cards.append(card)
        
        saved_cards = await self.bulk_save_objects(cards)
        
        # Create permissions matrix (each user gets access to some doors)
        permissions = []
        for i, user in enumerate(saved_users):
            # Each user gets access to doors based on their index
            accessible_doors = saved_doors[:i+1]  # User 0 gets 1 door, user 1 gets 2 doors, etc.
            for door in accessible_doors:
                permission = PermissionModelFactory.create_for_user_and_door(user.id, door.id)
                permissions.append(permission)
        
        saved_permissions = await self.bulk_save_objects(permissions)
        
        await self._commit_changes()
        
        return {
            'users': saved_users,
            'doors': saved_doors,
            'cards': saved_cards,
            'permissions': saved_permissions
        }
    
    async def seed_error_scenario_data(self) -> Dict[str, Any]:
        """Seed data for testing error scenarios."""
        logger.info("Seeding error scenario test data")
        
        # Create users with different statuses
        active_user = await self._save_object(UserModelFactory.create(
            email="error_active@test.com"
        ))
        
        inactive_user = await self._save_object(UserModelFactory.create_inactive(
            email="error_inactive@test.com"
        ))
        
        suspended_user = await self._save_object(UserModelFactory.create(
            email="error_suspended@test.com",
            is_active=False
        ))
        
        # Create doors with different statuses
        active_door = await self._save_object(DoorModelFactory.create(
            name="Error Test Active Door"
        ))
        
        inactive_door = await self._save_object(DoorModelFactory.create_inactive(
            name="Error Test Inactive Door"
        ))
        
        maintenance_door = await self._save_object(DoorModelFactory.create_maintenance(
            name="Error Test Maintenance Door"
        ))
        
        # Create cards with various statuses
        active_card = await self._save_object(CardModelFactory.create(
            user_id=active_user.id
        ))
        
        expired_card = await self._save_object(CardModelFactory.create_expired(
            user_id=active_user.id
        ))
        
        suspended_card = await self._save_object(CardModelFactory.create_suspended(
            user_id=active_user.id
        ))
        
        # Create some invalid permissions (for testing edge cases)
        valid_permission = await self._save_object(
            PermissionModelFactory.create_for_user_and_door(active_user.id, active_door.id)
        )
        
        expired_permission = await self._save_object(
            PermissionModelFactory.create_expired(
                user_id=active_user.id,
                door_id=active_door.id
            )
        )
        
        await self._commit_changes()
        
        return {
            'users': {
                'active': active_user,
                'inactive': inactive_user,
                'suspended': suspended_user
            },
            'doors': {
                'active': active_door,
                'inactive': inactive_door,
                'maintenance': maintenance_door
            },
            'cards': {
                'active': active_card,
                'expired': expired_card,
                'suspended': suspended_card
            },
            'permissions': {
                'valid': valid_permission,
                'expired': expired_permission
            }
        }
    
    async def seed_performance_test_data(self, user_count: int = 100, door_count: int = 20) -> Dict[str, Any]:
        """Seed large dataset for performance testing."""
        logger.info(f"Seeding performance test data: {user_count} users, {door_count} doors")
        
        # Create users in batches for better performance
        users = []
        for i in range(user_count):
            user = UserModelFactory.create(
                email=f"perf_user_{i}@test.com",
                full_name=f"Performance Test User {i}"
            )
            users.append(user)
        
        saved_users = await self.bulk_save_objects(users)
        logger.info(f"Created {len(saved_users)} users")
        
        # Create doors
        doors = []
        security_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        for i in range(door_count):
            door = DoorModelFactory.create(
                name=f"Performance Test Door {i}",
                security_level=security_levels[i % len(security_levels)],
                location=f"Building {i//10} - Floor {i%10}"
            )
            doors.append(door)
        
        saved_doors = await self.bulk_save_objects(doors)
        logger.info(f"Created {len(saved_doors)} doors")
        
        # Create cards for each user
        cards = []
        for user in saved_users:
            card = CardModelFactory.create(user_id=user.id)
            cards.append(card)
        
        saved_cards = await self.bulk_save_objects(cards)
        logger.info(f"Created {len(saved_cards)} cards")
        
        await self._commit_changes()
        
        return {
            'users': saved_users,
            'doors': saved_doors,
            'cards': saved_cards,
            'user_count': len(saved_users),
            'door_count': len(saved_doors),
            'card_count': len(saved_cards)
        }