class DomainError(Exception):
    """Base exception for domain-level errors."""
    pass

class RepositoryError(DomainError):
    """Exception raised for errors in the repository layer."""
    pass

class MqttAdapterError(DomainError):
    """Exception raised for errors in the MQTT adapter layer."""
    pass

# Add other specific domain exceptions as needed
class MqttMessageProcessingError(DomainError):
    """Exception raised when processing an MQTT message fails."""
    pass 