"""
Tests for the new test data factories and seeders.
"""
import pytest
from datetime import datetime, timezone
from uuid import UUID

from tests.factories import UserFactory, CardFactory, DoorFactory, PermissionFactory
from tests.factories import UserModelFactory, CardModelFactory, DoorModelFactory, PermissionModelFactory
from tests.seeders import TestScenarios, IntegrationSeeder
from tests.conftest import db_session

pytestmark = pytest.mark.asyncio


class TestEntityFactories:
    """Test the domain entity factories."""
    
    def test_user_factory_creates_valid_user(self):
        """Test that UserFactory creates a valid User entity."""
        user = UserFactory.create()
        
        assert user.id is not None
        assert isinstance(user.id, UUID)
        assert user.email.endswith('@test.example.com')
        assert user.full_name.startswith('Test User')
        assert len(user.roles) > 0
        assert user.status.value == 'active'
        assert isinstance(user.created_at, datetime)
    
    def test_user_factory_admin_creation(self):
        """Test that UserFactory can create admin users."""
        admin = UserFactory.create_admin()
        
        assert any(role.value == 'admin' for role in admin.roles)
        assert admin.email.startswith('admin_')
        assert 'Admin' in admin.full_name
    
    def test_card_factory_creates_valid_card(self):
        """Test that CardFactory creates a valid Card entity."""
        card = CardFactory.create()
        
        assert card.id is not None
        assert isinstance(card.id, UUID)
        assert card.card_id.startswith('CARD_')
        assert card.card_type.value == 'standard'
        assert card.status.value == 'active'
        assert card.valid_from <= datetime.now(timezone.utc)
        assert card.valid_until > datetime.now(timezone.utc)
    
    def test_card_factory_master_card(self):
        """Test that CardFactory can create master cards."""
        master_card = CardFactory.create_master()
        
        assert master_card.card_type.value == 'master'
        assert master_card.card_id.startswith('MASTER_')
        # Master cards should have longer validity
        assert (master_card.valid_until - master_card.valid_from).days > 365
    
    def test_door_factory_creates_valid_door(self):
        """Test that DoorFactory creates a valid Door entity."""
        door = DoorFactory.create()
        
        assert door.id is not None
        assert isinstance(door.id, UUID)
        assert door.name.startswith('TestDoor_')
        assert door.security_level == 'MEDIUM'
        assert door.status.value == 'active'
        assert door.max_attempts == 3
        assert door.lockout_duration == 300
    
    def test_door_factory_high_security(self):
        """Test that DoorFactory can create high security doors."""
        secure_door = DoorFactory.create_high_security()
        
        assert secure_door.security_level == 'HIGH'
        assert secure_door.requires_pin is True
        assert secure_door.max_attempts == 1
        assert secure_door.lockout_duration == 900
    
    def test_permission_factory_creates_valid_permission(self):
        """Test that PermissionFactory creates a valid Permission entity."""
        permission = PermissionFactory.create()
        
        assert permission.id is not None
        assert isinstance(permission.id, UUID)
        assert isinstance(permission.user_id, UUID)
        assert isinstance(permission.door_id, UUID)
        assert permission.status.value == 'active'
        assert permission.valid_from <= datetime.now(timezone.utc)
        assert permission.valid_until > datetime.now(timezone.utc)


class TestDatabaseModelFactories:
    """Test the database model factories."""
    
    def test_user_model_factory_creates_valid_model(self):
        """Test that UserModelFactory creates a valid UserModel."""
        user_model = UserModelFactory.create()
        
        assert user_model.id is not None
        assert isinstance(user_model.id, UUID)
        assert user_model.email.endswith('@test.example.com')
        assert user_model.hashed_password is not None
        assert user_model.is_active is True
        assert isinstance(user_model.roles, list)
    
    def test_card_model_factory_creates_valid_model(self):
        """Test that CardModelFactory creates a valid CardModel."""
        card_model = CardModelFactory.create()
        
        assert card_model.id is not None
        assert card_model.card_id.startswith('CARD_')
        assert card_model.card_type == 'standard'
        assert card_model.status == 'active'
    
    def test_door_model_factory_creates_valid_model(self):
        """Test that DoorModelFactory creates a valid DoorModel."""
        door_model = DoorModelFactory.create()
        
        assert door_model.id is not None
        assert door_model.name.startswith('TestDoor_')
        assert door_model.security_level == 'MEDIUM'
        assert door_model.status == 'active'


class TestSeederIntegration:
    """Test the database seeders."""
    
    async def test_integration_seeder_basic_data(self, db_session):
        """Test that IntegrationSeeder creates valid test data."""
        seeder = IntegrationSeeder(db_session)
        
        try:
            data = await seeder.seed_basic_integration_data()
            
            # Verify users
            assert 'admin_user' in data
            assert 'regular_user' in data
            assert data['admin_user'].email == 'integration_admin@test.com'
            assert data['regular_user'].email == 'integration_user@test.com'
            
            # Verify doors
            assert 'main_door' in data
            assert 'secure_door' in data
            assert data['main_door'].name == 'Integration Main Door'
            
            # Verify cards
            assert 'admin_card' in data
            assert 'user_card' in data
            
            # Verify permissions
            assert 'admin_main_permission' in data
            assert 'user_main_permission' in data
            
            # Verify objects were actually saved to database
            assert seeder.get_created_count() > 0
            
        finally:
            await seeder.cleanup()
    
    async def test_test_scenarios_basic_access(self, db_session):
        """Test that TestScenarios creates a basic access scenario."""
        scenarios = TestScenarios(db_session)
        
        try:
            data = await scenarios.seed('basic_access')
            
            # Verify scenario structure
            assert 'users' in data
            assert 'doors' in data
            assert 'cards' in data
            assert 'permissions' in data
            
            # Verify users
            assert 'admin' in data['users']
            assert 'regular_user' in data['users']
            
            # Verify doors
            assert 'main_door' in data['doors']
            assert 'server_door' in data['doors']
            
            # Verify admin has more permissions than regular user
            admin_perms = data['permissions']['admin_permissions']
            user_perms = data['permissions']['user_permissions']
            assert len(admin_perms) > len(user_perms)
            
        finally:
            await scenarios.cleanup()
    
    async def test_scenario_error_handling(self, db_session):
        """Test that scenarios handle unknown scenario names properly."""
        scenarios = TestScenarios(db_session)
        
        with pytest.raises(ValueError) as exc_info:
            await scenarios.seed('nonexistent_scenario')
        
        assert 'Unknown scenario' in str(exc_info.value)


class TestFactoryConsistency:
    """Test that factories create consistent and related data."""
    
    def test_related_entities_consistency(self):
        """Test that related entities have consistent IDs."""
        user = UserFactory.create()
        card = CardFactory.create_for_user(user.id)
        
        assert card.user_id == user.id
    
    def test_factory_uniqueness(self):
        """Test that factories create unique entities."""
        user1 = UserFactory.create()
        user2 = UserFactory.create()
        
        assert user1.id != user2.id
        assert user1.email != user2.email
        
        card1 = CardFactory.create()
        card2 = CardFactory.create()
        
        assert card1.id != card2.id
        assert card1.card_id != card2.card_id
    
    def test_factory_customization(self):
        """Test that factories allow customization."""
        custom_email = "custom@example.com"
        user = UserFactory.create(email=custom_email)
        
        assert user.email == custom_email
        
        custom_card_id = "CUSTOM123"
        card = CardFactory.create(card_id=custom_card_id)
        
        assert card.card_id == custom_card_id


class TestFactoryPerformance:
    """Test factory performance for bulk operations."""
    
    def test_bulk_entity_creation(self):
        """Test that factories can create entities efficiently."""
        import time
        
        start_time = time.time()
        
        # Create 100 users
        users = [UserFactory.create() for _ in range(100)]
        
        creation_time = time.time() - start_time
        
        assert len(users) == 100
        assert all(user.id is not None for user in users)
        # Should be fast (less than 1 second for 100 entities)
        assert creation_time < 1.0
    
    async def test_seeder_performance(self, db_session):
        """Test that seeders can handle moderate data volumes."""
        seeder = IntegrationSeeder(db_session)
        
        try:
            import time
            start_time = time.time()
            
            # Create performance test data (smaller scale for unit test)
            data = await seeder.seed_performance_test_data(user_count=10, door_count=5)
            
            creation_time = time.time() - start_time
            
            assert data['user_count'] == 10
            assert data['door_count'] == 5
            assert data['card_count'] == 10
            # Should complete reasonably quickly
            assert creation_time < 5.0
            
        finally:
            await seeder.cleanup()