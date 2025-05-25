import aiomqtt
import asyncio
import ssl
import logging
from typing import Callable, Optional, Set
from dataclasses import dataclass
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.ports.mqtt_client_port import MqttClientPort
from app.domain.exceptions import MqttAdapterError
from app.config import get_settings

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class MqttConfig:
    """MQTT connection configuration"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    keepalive: int = 60
    clean_session: bool = True
    client_id: Optional[str] = None
    max_queued_messages: int = 0  # 0 = unlimited
    qos: int = 1

class AiomqttAdapter(MqttClientPort):
    """Modern MQTT adapter using aiomqtt v2.0.0"""
    
    def __init__(self, message_handler: Callable[[str, str], None]):
        self.message_handler = message_handler
        self._client: Optional[aiomqtt.Client] = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._subscriptions: Set[str] = set()
        self._config = self._build_config()
        self._should_reconnect = True
        
    def _build_config(self) -> MqttConfig:
        """Build MQTT configuration from settings"""
        settings = get_settings()
        
        return MqttConfig(
            host=settings.MQTT_HOST,
            port=settings.MQTT_PORT,
            username=settings.MQTT_USERNAME,
            password=settings.MQTT_PASSWORD,
            use_tls=settings.USE_TLS,
            client_id=f"access_control_{asyncio.current_task().get_name()}" if asyncio.current_task() else None
        )
    
    @property
    def is_connected(self) -> bool:
        """Check if client is currently connected"""
        return (
            self._connection_state == ConnectionState.CONNECTED and 
            self._client is not None
        )
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type(aiomqtt.MqttError)
    )
    async def _create_client(self) -> aiomqtt.Client:
        """Create and configure MQTT client with retry logic"""
        logger.info("Creating MQTT client...")
        
        # TLS configuration
        tls_context = None
        if self._config.use_tls:
            logger.info("Configuring TLS context...")
            tls_context = ssl.create_default_context()
            tls_context.check_hostname = True
            tls_context.verify_mode = ssl.CERT_REQUIRED
        
        # Create client with aiomqtt v2 API
        logger.info("Initializing MQTT client with configuration...")
        client = aiomqtt.Client(
            hostname=self._config.host,
            port=self._config.port,
            username=self._config.username,
            password=self._config.password,
            tls_context=tls_context,
            keepalive=self._config.keepalive,
            clean_session=self._config.clean_session,
            max_queued_incoming_messages=self._config.max_queued_messages,
            max_queued_outgoing_messages=self._config.max_queued_messages
        )
        
        logger.info(f"MQTT client created successfully for {self._config.host}:{self._config.port}")
        return client
    
    async def connect_and_listen(self):
        """Main connection and message listening loop with reconnection"""
        logger.info("Starting MQTT connection and listen loop...")
        
        while self._should_reconnect:
            try:
                self._connection_state = ConnectionState.CONNECTING
                logger.info("Attempting to connect to MQTT broker...")
                
                # Create new client
                self._client = await self._create_client()
                
                # Connect and listen
                logger.info("Establishing MQTT connection...")
                async with self._client:
                    self._connection_state = ConnectionState.CONNECTED
                    logger.info("Successfully connected to MQTT broker")
                    
                    # Subscribe to test topic immediately after connection
                    try:
                        await self._client.subscribe("test/#", qos=self._config.qos)
                        logger.info("Successfully subscribed to test topic")
                    except Exception as e:
                        logger.error(f"Failed to subscribe to test topic: {e}")
                    
                    # Restore other subscriptions
                    await self._restore_subscriptions()
                    
                    # Listen for messages
                    logger.info("Starting message listening loop...")
                    await self._message_loop()
                    
            except aiomqtt.MqttError as e:
                self._connection_state = ConnectionState.FAILED
                logger.error(f"MQTT error during connection: {str(e)}", exc_info=True)
                
                if self._should_reconnect:
                    self._connection_state = ConnectionState.RECONNECTING
                    logger.info("Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    break
                    
            except asyncio.CancelledError:
                logger.info("MQTT connection task cancelled")
                break
                
            except Exception as e:
                self._connection_state = ConnectionState.FAILED
                logger.error(f"Unexpected error in MQTT connection: {str(e)}", exc_info=True)
                
                if self._should_reconnect:
                    await asyncio.sleep(10)
                else:
                    break
        
        self._connection_state = ConnectionState.DISCONNECTED
        logger.info("MQTT connection loop ended")
    
    async def _message_loop(self):
        """Main message processing loop"""
        try:
            logger.info("Starting MQTT message loop...")
            async for message in self._client.messages:
                logger.info(f"Received raw message on topic: {message.topic}")
                await self._handle_message(message)
        except aiomqtt.MqttError as e:
            logger.error(f"Error in message loop: {e}")
            raise
    
    async def _handle_message(self, message: aiomqtt.Message):
        """Handle incoming MQTT message safely"""
        try:
            topic = str(message.topic)
            payload = message.payload.decode('utf-8', errors='replace')
            
            logger.info(f"Processing MQTT message", extra={
                "topic": topic,
                "payload": payload,
                "qos": message.qos,
                "retain": message.retain
            })
            
            # Process message asynchronously to avoid blocking
            asyncio.create_task(
                self._safe_message_handler(topic, payload),
                name=f"mqtt_handler_{topic}"
            )
            
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}", exc_info=True)
    
    async def _safe_message_handler(self, topic: str, payload: str):
        """Safely execute message handler with error isolation"""
        try:
            await self.message_handler(topic, payload)
        except Exception as e:
            logger.error(f"Error in message handler for topic {topic}: {e}", exc_info=True)
    
    async def _restore_subscriptions(self):
        """Restore all subscriptions after reconnection"""
        if not self._subscriptions:
            logger.debug("No subscriptions to restore")
            return
        
        logger.info(f"Restoring {len(self._subscriptions)} subscriptions...")
        
        for topic in self._subscriptions:
            try:
                await self._client.subscribe(topic, qos=self._config.qos)
                logger.debug(f"Restored subscription to {topic}")
            except Exception as e:
                logger.error(f"Failed to restore subscription to {topic}: {e}")
    
    async def publish(self, topic: str, payload: str, qos: int = None, retain: bool = False):
        """Publish message to MQTT broker"""
        if not self.is_connected:
            logger.error("Cannot publish: MQTT client not connected")
            raise MqttAdapterError("MQTT client not connected")
        
        qos = qos if qos is not None else self._config.qos
        
        try:
            logger.info(f"Publishing message to topic: {topic}", extra={
                "payload": payload,
                "qos": qos,
                "retain": retain
            })
            
            await self._client.publish(
                topic=topic,
                payload=payload.encode('utf-8'),
                qos=qos,
                retain=retain
            )
            
            logger.info(f"Successfully published message to {topic}")
            
        except aiomqtt.MqttError as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            raise MqttAdapterError(f"Publish failed: {e}") from e
    
    async def subscribe(self, topic: str, qos: int = None):
        """Subscribe to MQTT topic"""
        qos = qos if qos is not None else self._config.qos
        
        # Add to subscription set for reconnection
        self._subscriptions.add(topic)
        
        if self.is_connected:
            try:
                await self._client.subscribe(topic, qos=qos)
                logger.info(f"Successfully subscribed to topic: {topic} with QoS {qos}")
            except aiomqtt.MqttError as e:
                logger.error(f"Failed to subscribe to {topic}: {e}")
                raise MqttAdapterError(f"Subscribe failed: {e}") from e
        else:
            logger.warning(f"Added {topic} to pending subscriptions (not connected)")
    
    async def unsubscribe(self, topic: str):
        """Unsubscribe from MQTT topic"""
        # Remove from subscription set
        self._subscriptions.discard(topic)
        
        if self.is_connected:
            try:
                await self._client.unsubscribe(topic)
                logger.info(f"Unsubscribed from {topic}")
            except aiomqtt.MqttError as e:
                logger.error(f"Failed to unsubscribe from {topic}: {e}")
                raise MqttAdapterError(f"Unsubscribe failed: {e}") from e
    
    async def disconnect(self):
        """Gracefully disconnect from MQTT broker"""
        self._should_reconnect = False
        self._connection_state = ConnectionState.DISCONNECTED
        
        if self._client:
            try:
                # aiomqtt v2 handles disconnection in context manager
                pass  # Client will disconnect when exiting context
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
        
        self._subscriptions.clear()
        logger.info("MQTT client disconnected")