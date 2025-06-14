"""
MQTT Service Factory for centralized service creation and configuration.
"""
import logging
from typing import Optional, Callable
from uuid import uuid4

from app.config import get_settings
from app.infrastructure.mqtt.adapters.asyncio_mqtt_adapter import AiomqttAdapter, MqttConfig
from app.domain.services.device_communication_service import DeviceCommunicationService
from app.domain.services.mqtt_device_handler import MqttDeviceHandler
from app.application.use_cases.access_use_cases import ValidateAccessUseCase
from app.domain.services.mqtt_message_service import MqttMessageService

logger = logging.getLogger(__name__)


class MqttServiceFactory:
    """Factory for creating configured MQTT services with proper dependency injection."""
    
    @staticmethod
    def create_mqtt_config() -> MqttConfig:
        """
        Creates an MqttConfig object using application settings.
        
        If a client ID is not specified in the settings, a deterministic client ID is generated for connection tracking.
        Returns:
            An MqttConfig instance populated with host, port, credentials, TLS usage, keepalive, clean session flag, client ID, maximum queued messages, and QoS.
        """
        settings = get_settings()
        
        # Generate a deterministic client ID for better connection tracking
        client_id = settings.MQTT_CLIENT_ID if hasattr(settings, 'MQTT_CLIENT_ID') and settings.MQTT_CLIENT_ID else None
        if not client_id:
            client_id = f"access_control_{uuid4().hex[:8]}"
        
        return MqttConfig(
            host=settings.MQTT_HOST,
            port=settings.MQTT_PORT,
            username=settings.MQTT_USERNAME,
            password=settings.MQTT_PASSWORD,
            use_tls=settings.USE_TLS,
            keepalive=settings.MQTT_KEEPALIVE,
            clean_session=settings.MQTT_CLEAN_SESSION,
            client_id=client_id,
            max_queued_messages=settings.MQTT_MAX_QUEUED_MESSAGES,
            qos=settings.MQTT_QOS
        )
    
    @staticmethod
    def create_mqtt_adapter(message_handler: Callable[[str, str], None]) -> AiomqttAdapter:
        """
        Creates an AiomqttAdapter instance configured with application MQTT settings.
        
        The adapter is initialized with the provided message handler and is set up using
        the generated MQTT configuration, including connection details and client ID.
        Returns the configured AiomqttAdapter.
        """
        config = MqttServiceFactory.create_mqtt_config()
        
        logger.info(
            f"Creating MQTT adapter with config: {config.host}:{config.port}, "
            f"client_id={config.client_id}, tls={config.use_tls}"
        )
        
        adapter = AiomqttAdapter(message_handler)
        adapter._config = config  # Override the internal config
        
        return adapter
    
    @staticmethod
    def create_device_communication_service(mqtt_adapter: AiomqttAdapter) -> DeviceCommunicationService:
        """
        Creates a DeviceCommunicationService using the provided MQTT adapter.
        
        Args:
            mqtt_adapter: The configured AiomqttAdapter to be used for device communication.
        
        Returns:
            An instance of DeviceCommunicationService initialized with the given MQTT adapter.
        """
        logger.info("Creating device communication service")
        return DeviceCommunicationService(mqtt_adapter)
    
    @staticmethod
    def create_device_handler(
        mqtt_message_service: MqttMessageService,
        device_communication_service: Optional[DeviceCommunicationService] = None,
        access_validation_use_case: Optional[ValidateAccessUseCase] = None
    ) -> MqttDeviceHandler:
        """
        Creates an MqttDeviceHandler with optional dependencies for device communication and access validation.
        
        Allows partial initialization of the device handler, enabling backward compatibility with existing initialization flows.
        """
        logger.info("Creating MQTT device handler")
        return MqttDeviceHandler(
            device_communication_service=device_communication_service,
            access_validation_use_case=access_validation_use_case,
            mqtt_message_service=mqtt_message_service
        )
    
    @staticmethod
    def create_complete_mqtt_services(
        mqtt_message_service: MqttMessageService
    ) -> tuple[AiomqttAdapter, DeviceCommunicationService, MqttDeviceHandler]:
        """
        Creates and wires a complete stack of MQTT services, including the adapter, device communication service, and device handler.
        
        The device handler is initialized without the access validation use case, which must be set separately to avoid circular dependencies.
        
        Args:
            mqtt_message_service: Service used by the device handler for processing MQTT messages.
        
        Returns:
            A tuple containing the MQTT adapter, device communication service, and device handler, fully connected for use.
        """
        logger.info("Creating complete MQTT service stack")
        
        # Create device handler first (partially initialized)
        device_handler = MqttServiceFactory.create_device_handler(mqtt_message_service)
        
        # Create MQTT adapter with device handler as message processor
        mqtt_adapter = MqttServiceFactory.create_mqtt_adapter(device_handler.handle_message)
        
        # Create device communication service
        device_communication_service = MqttServiceFactory.create_device_communication_service(mqtt_adapter)
        
        # Update device handler with communication service
        device_handler.device_service = device_communication_service
        
        logger.info("MQTT service stack created successfully")
        return mqtt_adapter, device_communication_service, device_handler


class MqttResilienceConfig:
    """Configuration class for MQTT resilience patterns."""
    
    def __init__(self):
        """
        Initializes MQTT resilience configuration parameters from application settings.
        
        Loads circuit breaker, connection resilience, retry, message buffering, and timeout
        settings to configure MQTT client resilience behavior.
        """
        settings = get_settings()
        
        # Circuit breaker settings
        self.circuit_breaker_threshold = getattr(settings, 'MQTT_CIRCUIT_BREAKER_THRESHOLD', 5)
        self.circuit_breaker_timeout = getattr(settings, 'MQTT_CIRCUIT_BREAKER_TIMEOUT', 60)
        
        # Connection resilience
        self.connection_pool_size = getattr(settings, 'MQTT_CONNECTION_POOL_SIZE', 3)
        self.health_check_interval = getattr(settings, 'MQTT_HEALTH_CHECK_INTERVAL', 30)
        
        # Retry configuration  
        self.retry_attempts = settings.MQTT_RETRY_ATTEMPTS
        self.retry_min_wait = settings.MQTT_RETRY_MIN_WAIT
        self.retry_max_wait = settings.MQTT_RETRY_MAX_WAIT
        
        # Message buffering
        self.message_buffer_size = getattr(settings, 'MQTT_MESSAGE_BUFFER_SIZE', 1000)
        
        # Timeouts
        self.command_timeout = settings.MQTT_COMMAND_TIMEOUT
        self.reconnect_delay = settings.MQTT_RECONNECT_DELAY