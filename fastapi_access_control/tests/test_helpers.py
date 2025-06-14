"""
Test helpers for UUID generation and common test patterns
"""
from uuid import UUID, uuid4


def create_test_uuid(seed: str) -> UUID:
    """Create consistent UUIDs for testing based on seed string"""
    # Create predictable UUIDs for testing
    uuid_map = {
        "user1": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
        "user2": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d480"),
        "card1": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d481"),
        "card2": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d482"),
        "door1": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d483"),
        "door2": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d484"),
        "permission1": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d485"),
        "permission2": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d486"),
        "mqtt1": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d487"),
        "nonexistent": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d999"),
    }
    
    return uuid_map.get(seed, uuid4())


# Common test UUIDs
TEST_USER_ID_1 = create_test_uuid("user1")
TEST_USER_ID_2 = create_test_uuid("user2")
TEST_CARD_ID_1 = create_test_uuid("card1")
TEST_CARD_ID_2 = create_test_uuid("card2")
TEST_DOOR_ID_1 = create_test_uuid("door1")
TEST_DOOR_ID_2 = create_test_uuid("door2")
TEST_PERMISSION_ID_1 = create_test_uuid("permission1")
TEST_PERMISSION_ID_2 = create_test_uuid("permission2")
TEST_MQTT_ID_1 = create_test_uuid("mqtt1")
TEST_NONEXISTENT_ID = create_test_uuid("nonexistent")