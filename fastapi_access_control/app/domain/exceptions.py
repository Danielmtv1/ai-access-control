class DomainError(Exception):
    """Base exception for domain-level errors."""
    pass


class RepositoryError(DomainError):
    """Exception raised for errors in the repository layer."""
    pass


class MqttAdapterError(DomainError):
    """Exception raised for errors in the MQTT adapter layer."""
    pass


class MqttMessageProcessingError(DomainError):
    """Exception raised when processing an MQTT message fails."""
    pass


# Entity Not Found Errors - Unified Hierarchy
class EntityNotFoundError(DomainError):
    """Base exception for when an entity is not found."""
    
    def __init__(self, entity_type: str, identifier: str, message: str = None):
        self.entity_type = entity_type
        self.identifier = identifier
        if message is None:
            message = f"{entity_type} with identifier '{identifier}' not found"
        super().__init__(message)


class CardNotFoundError(EntityNotFoundError):
    """Exception raised when a card is not found."""
    
    def __init__(self, card_id: str, message: str = None):
        super().__init__("Card", card_id, message)


class DoorNotFoundError(EntityNotFoundError):
    """Exception raised when a door is not found."""
    
    def __init__(self, door_id: str, message: str = None):
        super().__init__("Door", door_id, message)


class UserNotFoundError(EntityNotFoundError):
    """Exception raised when a user is not found."""
    
    def __init__(self, user_id: str, message: str = None):
        super().__init__("User", user_id, message)


class PermissionNotFoundError(EntityNotFoundError):
    """Exception raised when a permission is not found."""
    
    def __init__(self, permission_id: str, message: str = None):
        super().__init__("Permission", permission_id, message)


# Business Logic Validation Errors
class InvalidCardError(DomainError):
    """Exception raised when a card is invalid or inactive."""
    pass


class InvalidDoorError(DomainError):
    """Exception raised when a door is invalid or inaccessible."""
    pass


class AccessDeniedError(DomainError):
    """Exception raised when access is denied."""
    pass


class InvalidPinError(DomainError):
    """Exception raised when an invalid PIN is provided."""
    pass


class EntityAlreadyExistsError(DomainError):
    """Exception raised when trying to create an entity that already exists."""
    
    def __init__(self, entity_type: str, identifier: str, message: str = None):
        self.entity_type = entity_type
        self.identifier = identifier
        if message is None:
            message = f"{entity_type} with identifier '{identifier}' already exists"
        super().__init__(message)


class ValidationError(DomainError):
    """Exception raised for validation errors in business logic."""
    pass