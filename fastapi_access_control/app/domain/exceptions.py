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

# Access control exceptions
class EntityNotFoundError(DomainError):
    """Exception raised when an entity is not found."""
    pass

class InvalidCardError(DomainError):
    """Exception raised when a card is invalid or inactive."""
    pass

class InvalidDoorError(DomainError):
    """Exception raised when a door is invalid or inaccessible."""
    pass

class AccessDeniedError(DomainError):
    """Exception raised when access is denied."""
    pass