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
        """
        Initializes an EntityNotFoundError with entity type and identifier details.
        
        Args:
            entity_type: The type of entity that was not found.
            identifier: The unique identifier of the missing entity.
            message: Optional custom error message. If not provided, a default message is generated.
        """
        self.entity_type = entity_type
        self.identifier = identifier
        if message is None:
            message = f"{entity_type} with identifier '{identifier}' not found"
        super().__init__(message)


class CardNotFoundError(EntityNotFoundError):
    """Exception raised when a card is not found."""
    
    def __init__(self, card_id: str, message: str = None):
        """
        Initializes a CardNotFoundError for a missing card entity.
        
        Args:
            card_id: The identifier of the card that was not found.
            message: Optional custom error message.
        """
        super().__init__("Card", card_id, message)


class DoorNotFoundError(EntityNotFoundError):
    """Exception raised when a door is not found."""
    
    def __init__(self, door_id: str, message: str = None):
        """
        Initializes a DoorNotFoundError for a missing door entity.
        
        Args:
            door_id: The unique identifier of the door.
            message: Optional custom error message.
        """
        super().__init__("Door", door_id, message)


class UserNotFoundError(EntityNotFoundError):
    """Exception raised when a user is not found."""
    
    def __init__(self, user_id: str, message: str = None):
        """
        Initializes a UserNotFoundError for a missing user entity.
        
        Args:
            user_id: The identifier of the user that was not found.
            message: Optional custom error message.
        """
        super().__init__("User", user_id, message)


class PermissionNotFoundError(EntityNotFoundError):
    """Exception raised when a permission is not found."""
    
    def __init__(self, permission_id: str, message: str = None):
        """
        Initializes a PermissionNotFoundError for a missing permission entity.
        
        Args:
            permission_id: The identifier of the missing permission.
            message: Optional custom error message.
        """
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
        """
        Initializes an EntityAlreadyExistsError with entity type and identifier.
        
        Args:
            entity_type: The type of entity that already exists.
            identifier: The unique identifier of the entity.
            message: Optional custom error message. If not provided, a default message is generated.
        """
        self.entity_type = entity_type
        self.identifier = identifier
        if message is None:
            message = f"{entity_type} with identifier '{identifier}' already exists"
        super().__init__(message)


class ValidationError(DomainError):
    """Exception raised for validation errors in business logic."""
    pass