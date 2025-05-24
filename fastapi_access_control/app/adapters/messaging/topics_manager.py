import re

class MQTTTopicsManager:
    BASE_TOPIC = "access"

    @staticmethod
    def get_door_events_topic(door_id: str) -> str:
        """Generates the topic for door events."""
        return f"{MQTTTopicsManager.BASE_TOPIC}/doors/{door_id}/events"

    @staticmethod
    def get_card_scans_topic(card_id: str) -> str:
        """Generates the topic for card scans."""
        return f"{MQTTTopicsManager.BASE_TOPIC}/cards/{card_id}/scans"

    @staticmethod
    def send_device_command_topic(device_id: str) -> str:
        """Generates the topic for sending device commands."""
        return f"{MQTTTopicsManager.BASE_TOPIC}/commands/{device_id}"

    @staticmethod
    def get_device_status_topic(device_id: str) -> str:
        """Generates the topic for device status updates."""
        return f"{MQTTTopicsManager.BASE_TOPIC}/status/{device_id}"

    @staticmethod
    def parse_topic(topic: str) -> dict | None:
        """Parses a topic string and extracts components."""
        match = re.match(f"^{MQTTTopicsManager.BASE_TOPIC}/([^/]+)/([^/]+)(?:/(.+))?$", topic)
        if match:
            topic_type = match.group(1)
            topic_id = match.group(2)
            action = match.group(3) if match.group(3) else None
            return {
                "type": topic_type,
                "id": topic_id,
                "action": action
            }
        return None

    @staticmethod
    def validate_topic(topic: str) -> bool:
        """Validates if a topic follows the expected structure."""
        return topic.startswith(f"{MQTTTopicsManager.BASE_TOPIC}/") and len(topic.split("/")) >= 3 