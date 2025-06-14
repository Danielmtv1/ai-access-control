"""
Pre-defined test scenarios for consistent database seeding.
"""
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..factories import UserModelFactory, CardModelFactory, DoorModelFactory, PermissionModelFactory
from .base_seeder import TransactionalSeeder

logger = logging.getLogger(__name__)


class TestScenarios(TransactionalSeeder):
    """Pre-defined test scenarios for different testing needs."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.scenarios = {
            'basic_access': self._basic_access_scenario,
            'high_security': self._high_security_scenario,
            'multi_user': self._multi_user_scenario,
            'expired_cards': self._expired_cards_scenario,
            'complex_permissions': self._complex_permissions_scenario,
            'emergency_scenario': self._emergency_scenario,
            'visitor_access': self._visitor_access_scenario
        }
    
    async def seed(self, scenario_name: str = 'basic_access') -> Dict[str, Any]:
        """Seed database with a specific scenario."""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(self.scenarios.keys())}")
        
        logger.info(f"Seeding scenario: {scenario_name}")
        result = await self.scenarios[scenario_name]()
        logger.info(f"Scenario '{scenario_name}' seeded successfully")
        return result
    
    async def _basic_access_scenario(self) -> Dict[str, Any]:
        """Basic scenario: 1 admin, 2 users, 3 doors, basic permissions."""
        # Create users
        admin_user = await self._save_object(UserModelFactory.create_admin(
            email="admin@test.com",
            full_name="Test Admin"
        ))
        
        regular_user = await self._save_object(UserModelFactory.create(
            email="user@test.com", 
            full_name="Test User"
        ))
        
        # Create doors
        main_door = await self._save_object(DoorModelFactory.create(
            name="Main Entrance",
            security_level="LOW"
        ))
        
        office_door = await self._save_object(DoorModelFactory.create(
            name="Office Area",
            security_level="MEDIUM"
        ))
        
        server_door = await self._save_object(DoorModelFactory.create_high_security(
            name="Server Room"
        ))
        
        # Create cards
        admin_card = await self._save_object(CardModelFactory.create_master(
            user_id=admin_user.id
        ))
        
        user_card = await self._save_object(CardModelFactory.create(
            user_id=regular_user.id
        ))
        
        # Create permissions
        # Admin has access to all doors
        admin_permissions = []
        for door in [main_door, office_door, server_door]:
            permission = await self._save_object(PermissionModelFactory.create_for_user_and_door(
                admin_user.id, door.id
            ))
            admin_permissions.append(permission)
        
        # Regular user has access to main and office doors only
        user_permissions = []
        for door in [main_door, office_door]:
            permission = await self._save_object(PermissionModelFactory.create_for_user_and_door(
                regular_user.id, door.id
            ))
            user_permissions.append(permission)
        
        return {
            'users': {
                'admin': admin_user,
                'regular_user': regular_user
            },
            'doors': {
                'main_door': main_door,
                'office_door': office_door,
                'server_door': server_door
            },
            'cards': {
                'admin_card': admin_card,
                'user_card': user_card
            },
            'permissions': {
                'admin_permissions': admin_permissions,
                'user_permissions': user_permissions
            }
        }
    
    async def _high_security_scenario(self) -> Dict[str, Any]:
        """High security scenario: Multiple security levels, PIN requirements."""
        # Create users with different roles
        admin = await self._save_object(UserModelFactory.create_admin())
        security_operator = await self._save_object(UserModelFactory.create_operator())
        visitor = await self._save_object(UserModelFactory.create())
        
        # Create doors with different security levels
        public_door = await self._save_object(DoorModelFactory.create_low_security(
            name="Public Area"
        ))
        
        restricted_door = await self._save_object(DoorModelFactory.create(
            name="Restricted Area",
            security_level="MEDIUM",
            requires_pin=True
        ))
        
        vault_door = await self._save_object(DoorModelFactory.create_critical_security(
            name="Vault"
        ))
        
        # Create cards
        admin_card = await self._save_object(CardModelFactory.create_master(
            user_id=admin.id
        ))
        
        operator_card = await self._save_object(CardModelFactory.create(
            user_id=security_operator.id
        ))
        
        visitor_card = await self._save_object(CardModelFactory.create_temporary(
            user_id=visitor.id
        ))
        
        # Create hierarchical permissions
        permissions = []
        
        # Admin: All access
        for door in [public_door, restricted_door, vault_door]:
            perm = await self._save_object(PermissionModelFactory.create_for_user_and_door(
                admin.id, door.id
            ))
            permissions.append(perm)
        
        # Operator: Public and restricted
        for door in [public_door, restricted_door]:
            perm = await self._save_object(PermissionModelFactory.create_for_user_and_door(
                security_operator.id, door.id
            ))
            permissions.append(perm)
        
        # Visitor: Public only
        perm = await self._save_object(PermissionModelFactory.create_for_user_and_door(
            visitor.id, public_door.id
        ))
        permissions.append(perm)
        
        return {
            'users': {'admin': admin, 'operator': security_operator, 'visitor': visitor},
            'doors': {'public': public_door, 'restricted': restricted_door, 'vault': vault_door},
            'cards': {'admin_card': admin_card, 'operator_card': operator_card, 'visitor_card': visitor_card},
            'permissions': permissions
        }
    
    async def _multi_user_scenario(self) -> Dict[str, Any]:
        """Multi-user scenario: 10 users, 5 doors, various permissions."""
        users = []
        cards = []
        
        # Create 10 users with cards
        for i in range(10):
            user = await self._save_object(UserModelFactory.create(
                email=f"user{i}@test.com",
                full_name=f"Test User {i}"
            ))
            users.append(user)
            
            card = await self._save_object(CardModelFactory.create(
                user_id=user.id
            ))
            cards.append(card)
        
        # Create 5 doors
        doors = []
        for i in range(5):
            door = await self._save_object(DoorModelFactory.create(
                name=f"Door {i}",
                location=f"Floor {i//2 + 1}"
            ))
            doors.append(door)
        
        # Create random permissions (each user gets access to 2-4 doors)
        permissions = []
        import random
        
        for user in users:
            accessible_doors = random.sample(doors, random.randint(2, 4))
            for door in accessible_doors:
                perm = await self._save_object(PermissionModelFactory.create_for_user_and_door(
                    user.id, door.id
                ))
                permissions.append(perm)
        
        return {
            'users': users,
            'doors': doors,
            'cards': cards,
            'permissions': permissions
        }
    
    async def _expired_cards_scenario(self) -> Dict[str, Any]:
        """Scenario with expired and suspended cards."""
        user = await self._save_object(UserModelFactory.create())
        door = await self._save_object(DoorModelFactory.create())
        
        # Create cards with different statuses
        active_card = await self._save_object(CardModelFactory.create(user_id=user.id))
        expired_card = await self._save_object(CardModelFactory.create_expired(user_id=user.id))
        suspended_card = await self._save_object(CardModelFactory.create_suspended(user_id=user.id))
        lost_card = await self._save_object(CardModelFactory.create_lost(user_id=user.id))
        
        # Create permissions
        permission = await self._save_object(PermissionModelFactory.create_for_user_and_door(
            user.id, door.id
        ))
        
        return {
            'user': user,
            'door': door,
            'cards': {
                'active': active_card,
                'expired': expired_card,
                'suspended': suspended_card,
                'lost': lost_card
            },
            'permission': permission
        }
    
    async def _complex_permissions_scenario(self) -> Dict[str, Any]:
        """Complex permissions with schedules and expiration dates."""
        # Users
        day_worker = await self._save_object(UserModelFactory.create(
            email="dayworker@test.com"
        ))
        night_worker = await self._save_object(UserModelFactory.create(
            email="nightworker@test.com"
        ))
        weekend_worker = await self._save_object(UserModelFactory.create(
            email="weekend@test.com"
        ))
        
        # Doors
        office = await self._save_object(DoorModelFactory.create_with_schedule())
        warehouse = await self._save_object(DoorModelFactory.create_24_7_access())
        
        # Cards
        cards = []
        for user in [day_worker, night_worker, weekend_worker]:
            card = await self._save_object(CardModelFactory.create(user_id=user.id))
            cards.append(card)
        
        # Complex permissions with different schedules
        day_permission = await self._save_object(PermissionModelFactory.create_with_schedule(
            user_id=day_worker.id,
            door_id=office.id
        ))
        
        weekend_permission = await self._save_object(PermissionModelFactory.create_weekend_only(
            user_id=weekend_worker.id,
            door_id=warehouse.id
        ))
        
        all_access_permission = await self._save_object(PermissionModelFactory.create_with_24_7_access(
            user_id=night_worker.id,
            door_id=warehouse.id
        ))
        
        return {
            'users': {
                'day_worker': day_worker,
                'night_worker': night_worker,
                'weekend_worker': weekend_worker
            },
            'doors': {'office': office, 'warehouse': warehouse},
            'cards': cards,
            'permissions': [day_permission, weekend_permission, all_access_permission]
        }
    
    async def _emergency_scenario(self) -> Dict[str, Any]:
        """Emergency scenario with emergency exits and locked doors."""
        admin = await self._save_object(UserModelFactory.create_admin())
        regular_user = await self._save_object(UserModelFactory.create())
        
        # Doors
        emergency_exit = await self._save_object(DoorModelFactory.create_emergency_exit())
        locked_door = await self._save_object(DoorModelFactory.create_emergency_locked())
        maintenance_door = await self._save_object(DoorModelFactory.create_maintenance())
        
        # Cards
        admin_card = await self._save_object(CardModelFactory.create_master(user_id=admin.id))
        user_card = await self._save_object(CardModelFactory.create(user_id=regular_user.id))
        
        # Permissions (admin can access maintenance, users can't access locked door)
        admin_permission = await self._save_object(PermissionModelFactory.create_for_user_and_door(
            admin.id, maintenance_door.id
        ))
        
        return {
            'users': {'admin': admin, 'user': regular_user},
            'doors': {
                'emergency_exit': emergency_exit,
                'locked_door': locked_door,
                'maintenance_door': maintenance_door
            },
            'cards': {'admin_card': admin_card, 'user_card': user_card},
            'permissions': [admin_permission]
        }
    
    async def _visitor_access_scenario(self) -> Dict[str, Any]:
        """Visitor access scenario with temporary permissions."""
        host = await self._save_object(UserModelFactory.create())
        visitor = await self._save_object(UserModelFactory.create())
        
        # Doors
        lobby = await self._save_object(DoorModelFactory.create_low_security(name="Lobby"))
        meeting_room = await self._save_object(DoorModelFactory.create(name="Meeting Room"))
        
        # Cards
        host_card = await self._save_object(CardModelFactory.create(user_id=host.id))
        visitor_card = await self._save_object(CardModelFactory.create_visitor(user_id=visitor.id))
        
        # Permissions
        host_permission = await self._save_object(PermissionModelFactory.create_for_user_and_door(
            host.id, meeting_room.id
        ))
        
        visitor_permission = await self._save_object(PermissionModelFactory.create_temporary(
            user_id=visitor.id,
            door_id=lobby.id
        ))
        
        return {
            'users': {'host': host, 'visitor': visitor},
            'doors': {'lobby': lobby, 'meeting_room': meeting_room},
            'cards': {'host_card': host_card, 'visitor_card': visitor_card},
            'permissions': [host_permission, visitor_permission]
        }