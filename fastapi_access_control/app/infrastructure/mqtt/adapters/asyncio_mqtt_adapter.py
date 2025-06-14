import aiomqtt
import asyncio
import ssl
import logging
from typing import Callable, Optional, Set, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from collections import deque
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.ports.mqtt_client_port import MqttClientPort
from app.domain.exceptions import MqttAdapterError
from app.config import get_settings
from app.infrastructure.observability.metrics import mqtt_connection_status


logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class MqttConfig:
    """MQTT connection configuration with resilience settings"""
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
    
    # Resilience configuration
    retry_attempts: int = 5
    retry_min_wait: int = 1
    retry_max_wait: int = 60
    connection_timeout: int = 30
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    message_buffer_size: int = 1000
    health_check_interval: int = 30


@dataclass
class CircuitBreakerState:
    """Circuit breaker state management"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    is_open: bool = False
    
    def record_success(self):
        """
        Resets the circuit breaker state after a successful operation.
        
        Sets the failure count to zero, closes the circuit, and clears the last failure timestamp.
        """
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None
    
    def record_failure(self, threshold: int, timeout: int):
        """
        Records a failed operation and updates the circuit breaker state.
        
        If the number of consecutive failures reaches or exceeds the specified threshold, the circuit breaker is opened to prevent further attempts until the timeout elapses.
        
        Args:
            threshold: The number of failures required to open the circuit breaker.
            timeout: The duration (in seconds) the circuit remains open before allowing new attempts.
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.failure_count >= threshold:
            self.is_open = True
    
    def can_attempt(self, timeout: int) -> bool:
        """
        Determines whether a new connection attempt is permitted based on the circuit breaker state.
        
        If the circuit is open, allows a new attempt only after the specified timeout has elapsed since the last failure. Resets the circuit breaker if the timeout has passed.
        
        Args:
            timeout: The minimum number of seconds to wait before allowing a new attempt after the circuit is opened.
        
        Returns:
            True if a new attempt is allowed, False otherwise.
        """
        if not self.is_open:
            return True
        
        if self.last_failure_time:
            elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
            if elapsed >= timeout:
                # Reset circuit breaker for a new attempt
                self.is_open = False
                return True
        
        return False


@dataclass
class MessageBuffer:
    """Buffer for messages during connection outages"""
    messages: deque = field(default_factory=deque)
    max_size: int = 1000
    
    def add_message(self, topic: str, payload: str, qos: int = 1, retain: bool = False):
        """
        Adds a message to the buffer, removing the oldest if the buffer is full.
        
        If the buffer has reached its maximum size, the oldest message is discarded to make room for the new one.
        """
        if len(self.messages) >= self.max_size:
            # Remove oldest message to make room
            self.messages.popleft()
        
        self.messages.append({
            'topic': topic,
            'payload': payload,
            'qos': qos,
            'retain': retain,
            'timestamp': datetime.now(timezone.utc)
        })
    
    def get_buffered_messages(self) -> list:
        """
        Retrieves and clears all buffered messages.
        
        Returns:
            A list of all messages that were buffered prior to this call.
        """
        messages = list(self.messages)
        self.messages.clear()
        return messages
    
    def clear(self):
        """
        Removes all messages from the buffer.
        """
        self.messages.clear()
    
    @property
    def count(self) -> int:
        """
        Returns the current number of messages stored in the buffer.
        """
        return len(self.messages)

class AiomqttAdapter(MqttClientPort):
    """Modern MQTT adapter with enhanced resilience patterns"""
    
    def __init__(self, message_handler: Callable[[str, str], None]):
        """
        Initializes the AiomqttAdapter with message handling, configuration, and resilience features.
        
        Args:
            message_handler: Callback function to process incoming MQTT messages, accepting topic and payload as arguments.
        
        Initializes internal state, including MQTT client, connection state, subscriptions, configuration, circuit breaker, message buffer, health check timestamp, connection metrics, and reconnection control.
        """
        self.message_handler = message_handler
        self._client: Optional[aiomqtt.Client] = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._subscriptions: Set[str] = set()
        self._config = self._build_config()
        self._should_reconnect = True
        
        # Resilience components
        self._circuit_breaker = CircuitBreakerState()
        self._message_buffer = MessageBuffer(max_size=self._config.message_buffer_size)
        self._last_health_check = datetime.now(timezone.utc)
        self._connection_start_time: Optional[datetime] = None
        self._total_messages_sent = 0
        self._total_messages_received = 0
        self._connection_attempts = 0
        
    def _build_config(self) -> MqttConfig:
        """
        Constructs and returns an MQTT configuration object populated with connection and resilience parameters from application settings.
        
        Returns:
            MqttConfig: An instance containing all MQTT connection and resilience settings, including host, port, credentials, TLS usage, keepalive, retry and circuit breaker parameters, message buffer size, and health check interval.
        """
        settings = get_settings()
        
        # Generate deterministic client ID
        client_id = getattr(settings, 'MQTT_CLIENT_ID', None)
        if not client_id:
            import uuid
            client_id = f"access_control_{uuid.uuid4().hex[:8]}"
        
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
            qos=settings.MQTT_QOS,
            retry_attempts=settings.MQTT_RETRY_ATTEMPTS,
            retry_min_wait=settings.MQTT_RETRY_MIN_WAIT,
            retry_max_wait=settings.MQTT_RETRY_MAX_WAIT,
            connection_timeout=settings.MQTT_COMMAND_TIMEOUT,
            circuit_breaker_threshold=getattr(settings, 'MQTT_CIRCUIT_BREAKER_THRESHOLD', 5),
            circuit_breaker_timeout=getattr(settings, 'MQTT_CIRCUIT_BREAKER_TIMEOUT', 60),
            message_buffer_size=getattr(settings, 'MQTT_MESSAGE_BUFFER_SIZE', 1000),
            health_check_interval=getattr(settings, 'MQTT_HEALTH_CHECK_INTERVAL', 30)
        )
    
    @property
    def is_connected(self) -> bool:
        """
        Returns True if the MQTT client is currently connected and initialized.
        """
        return (
            self._connection_state == ConnectionState.CONNECTED and 
            self._client is not None
        )
    
    @property
    def connection_stats(self) -> Dict[str, Any]:
        """
        Returns a dictionary of current connection statistics and metrics for monitoring.
        
        The returned statistics include connection state, uptime, message counts, connection attempts, buffered message count, circuit breaker status, and active subscription count.
         
        Returns:
            A dictionary containing connection state, uptime in seconds, total messages sent and received, connection attempts, number of buffered messages, circuit breaker status and failure count, and the number of active subscriptions.
        """
        uptime = None
        if self._connection_start_time:
            uptime = (datetime.now(timezone.utc) - self._connection_start_time).total_seconds()
        
        return {
            'state': self._connection_state.value,
            'connected': self.is_connected,
            'uptime_seconds': uptime,
            'total_messages_sent': self._total_messages_sent,
            'total_messages_received': self._total_messages_received,
            'connection_attempts': self._connection_attempts,
            'buffered_messages': self._message_buffer.count,
            'circuit_breaker_open': self._circuit_breaker.is_open,
            'circuit_breaker_failures': self._circuit_breaker.failure_count,
            'subscriptions_count': len(self._subscriptions)
        }
    
    def _check_circuit_breaker(self) -> bool:
        """
        Determines whether connection attempts are permitted by the circuit breaker.
        
        Returns:
            True if a connection attempt is allowed; False if the circuit breaker is open and blocking attempts.
        """
        can_attempt = self._circuit_breaker.can_attempt(self._config.circuit_breaker_timeout)
        if not can_attempt:
            logger.warning(
                f"Circuit breaker OPEN - blocking connection attempt. "
                f"Failures: {self._circuit_breaker.failure_count}, "
                f"Last failure: {self._circuit_breaker.last_failure_time}"
            )
        return can_attempt
    
    async def _create_client(self) -> aiomqtt.Client:
        """
        Creates and configures an MQTT client instance based on the current adapter settings.
        
        Returns:
            An initialized aiomqtt.Client configured with connection, authentication, and TLS parameters.
        """
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
        """
        Manages the MQTT connection lifecycle, including automatic reconnection, circuit breaker enforcement, message replay, and subscription restoration.
        
        Continuously attempts to connect to the MQTT broker while reconnection is enabled. Applies circuit breaker logic to prevent repeated failed attempts, uses exponential backoff on failures, and restores subscriptions and buffered messages upon successful reconnection. Handles connection errors, cancellation, and shutdown gracefully.
        """
        logger.info("Starting MQTT connection and listen loop...")
        
        while self._should_reconnect:
            # Check circuit breaker before attempting connection
            if not self._check_circuit_breaker():
                logger.warning("Circuit breaker open - waiting before next attempt")
                await asyncio.sleep(self._config.circuit_breaker_timeout)
                continue
            
            try:
                self._connection_state = ConnectionState.CONNECTING
                self._connection_attempts += 1
                mqtt_connection_status.set(1)  # Reset connection status
                logger.info(f"Attempting to connect to MQTT broker (attempt {self._connection_attempts})...")
                
                # Create new client with timeout
                self._client = await asyncio.wait_for(
                    self._create_client(),
                    timeout=self._config.connection_timeout
                )
                
                # Connect and listen
                logger.info("Establishing MQTT connection...")
                async with self._client:
                    self._connection_state = ConnectionState.CONNECTED
                    logger.info("Successfully connected to MQTT broker")
                    
                    # Record successful connection
                    self._circuit_breaker.record_success()
                    self._connection_start_time = datetime.now(timezone.utc)
                    logger.info("Successfully connected to MQTT broker")
                    
                    # Replay any buffered messages
                    await self._replay_buffered_messages()
                    
                    # Restore other subscriptions
                    await self._restore_subscriptions()
                    
                    # Listen for messages
                    logger.info("Starting message listening loop...")
                    await self._message_loop()
                    
            except aiomqtt.MqttError as e:
                self._connection_state = ConnectionState.FAILED
                mqtt_connection_status.set(0)
                
                # Record failure in circuit breaker
                self._circuit_breaker.record_failure(
                    self._config.circuit_breaker_threshold,
                    self._config.circuit_breaker_timeout
                )
                
                logger.error(f"MQTT error during connection: {str(e)}", exc_info=True)
                
                if self._should_reconnect and self._check_circuit_breaker():
                    self._connection_state = ConnectionState.RECONNECTING
                    # Exponential backoff with jitter
                    wait_time = min(self._config.retry_min_wait * (2 ** min(self._connection_attempts, 6)), self._config.retry_max_wait)
                    logger.info(f"Reconnecting in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.warning("Not attempting reconnection due to circuit breaker or shutdown")
                    break
                    
            except asyncio.CancelledError:
                logger.info("MQTT connection task cancelled")
                break
                
            except Exception as e:
                self._connection_state = ConnectionState.FAILED
                self._circuit_breaker.record_failure(
                    self._config.circuit_breaker_threshold,
                    self._config.circuit_breaker_timeout
                )
                logger.error(f"Unexpected error in MQTT connection: {str(e)}", exc_info=True)
                
                if self._should_reconnect and self._check_circuit_breaker():
                    await asyncio.sleep(10)
                else:
                    break
            
            finally:
                self._connection_attempts += 1
        
        self._connection_state = ConnectionState.DISCONNECTED
        logger.info("MQTT connection loop ended")
    
    async def _message_loop(self):
        """
        Continuously processes incoming MQTT messages from the client and dispatches them for handling.
        
        Iterates asynchronously over messages received from the MQTT broker, logging each message and passing it to the internal handler. Raises an exception if an MQTT error occurs.
        """
        try:
            logger.info("Starting MQTT message loop...")
            async for message in self._client.messages:
                logger.info(f"Received raw message on topic: {message.topic}")
                await self._handle_message(message)
        except aiomqtt.MqttError as e:
            logger.error(f"Error in message loop: {e}")
            raise
    
    async def _handle_message(self, message: aiomqtt.Message):
        """
        Processes an incoming MQTT message, updates metrics, and dispatches it to the message handler asynchronously.
        
        Args:
            message: The received MQTT message to process.
        """
        try:
            topic = str(message.topic)
            payload = message.payload.decode('utf-8', errors='replace')
            
            # Increment message counter
            self._total_messages_received += 1
            
            logger.info(f"Processing MQTT message", extra={
                "topic": topic,
                "payload": payload,
                "qos": message.qos,
                "retain": message.retain,
                "total_received": self._total_messages_received
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
        """
        Restores all previously subscribed topics after reconnecting to the MQTT broker.
        
        Attempts to resubscribe to each topic in the internal subscription set using the configured QoS level. Logs errors if any subscription fails.
        """
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
        """
        Publishes a message to the MQTT broker, buffering it if offline or on failure.
        
        If the client is not connected, the message is added to an internal buffer for later delivery. If publishing fails due to an MQTT error, the message is also buffered and an exception is raised.
        
        Args:
            topic: The MQTT topic to publish to.
            payload: The message payload.
            qos: The Quality of Service level for the message. If not specified, the default from configuration is used.
            retain: Whether the message should be retained by the broker.
        
        Raises:
            MqttAdapterError: If publishing fails while connected.
        """
        qos = qos if qos is not None else self._config.qos
        
        if not self.is_connected:
            # Buffer message for later delivery
            self._message_buffer.add_message(topic, payload, qos, retain)
            logger.warning(
                f"MQTT not connected - buffered message for topic: {topic}. "
                f"Buffer size: {self._message_buffer.count}"
            )
            return
        
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
            
            self._total_messages_sent += 1
            logger.info(f"Successfully published message to {topic} (total sent: {self._total_messages_sent})")
            
        except aiomqtt.MqttError as e:
            # Buffer failed message for retry
            self._message_buffer.add_message(topic, payload, qos, retain)
            logger.error(f"Failed to publish to {topic}: {e} - message buffered for retry")
            raise MqttAdapterError(f"Publish failed: {e}") from e
    
    async def subscribe(self, topic: str, qos: int = None):
        """
        Subscribes to a specified MQTT topic and manages subscription state.
        
        If the client is connected, attempts to subscribe immediately; otherwise, adds the topic to a pending subscriptions set for automatic restoration upon reconnection.
        
        Args:
            topic: The MQTT topic to subscribe to.
            qos: The Quality of Service level for the subscription. If not specified, uses the default from configuration.
        
        Raises:
            MqttAdapterError: If the subscription attempt fails while connected.
        """
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
        """
        Unsubscribes from a specified MQTT topic.
        
        Removes the topic from the internal subscription set and, if connected, sends an unsubscribe request to the MQTT broker. Raises a MqttAdapterError if the unsubscribe operation fails.
        """
        # Remove from subscription set
        self._subscriptions.discard(topic)
        
        if self.is_connected:
            try:
                await self._client.unsubscribe(topic)
                logger.info(f"Unsubscribed from {topic}")
            except aiomqtt.MqttError as e:
                logger.error(f"Failed to unsubscribe from {topic}: {e}")
                raise MqttAdapterError(f"Unsubscribe failed: {e}") from e
    
    async def _replay_buffered_messages(self):
        """
        Attempts to publish all messages buffered during connection outages.
        
        Retrieves messages from the buffer and publishes them to their respective topics. Messages that fail to publish are re-buffered for future attempts.
        """
        buffered_messages = self._message_buffer.get_buffered_messages()
        
        if not buffered_messages:
            return
        
        logger.info(f"Replaying {len(buffered_messages)} buffered messages")
        
        for msg in buffered_messages:
            try:
                await self._client.publish(
                    topic=msg['topic'],
                    payload=msg['payload'].encode('utf-8'),
                    qos=msg['qos'],
                    retain=msg['retain']
                )
                self._total_messages_sent += 1
                logger.debug(f"Replayed buffered message to {msg['topic']}")
            except Exception as e:
                logger.error(f"Failed to replay message to {msg['topic']}: {e}")
                # Re-buffer failed message
                self._message_buffer.add_message(
                    msg['topic'], msg['payload'], msg['qos'], msg['retain']
                )
    
    async def perform_health_check(self) -> bool:
        """
        Performs a health check by publishing a heartbeat message to a system topic.
        
        Returns:
            True if the heartbeat message was published successfully; False otherwise.
        """
        if not self.is_connected:
            return False
        
        try:
            heartbeat_topic = "system/heartbeat"
            heartbeat_payload = f"{{\"client_id\": \"{self._config.client_id}\", \"timestamp\": \"{datetime.now(timezone.utc).isoformat()}\"}}"
            
            await self._client.publish(
                topic=heartbeat_topic,
                payload=heartbeat_payload.encode('utf-8'),
                qos=0
            )
            
            self._last_health_check = datetime.now(timezone.utc)
            logger.debug("Health check completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def disconnect(self):
        """
        Gracefully disconnects the client from the MQTT broker.
        
        Stops reconnection attempts, updates connection state, logs session statistics, clears subscriptions and buffered messages, and ensures a clean shutdown.
        """
        logger.info("Starting graceful MQTT disconnect...")
        
        self._should_reconnect = False
        self._connection_state = ConnectionState.DISCONNECTED
        
        # Log final statistics
        stats = self.connection_stats
        logger.info(f"MQTT session statistics: {stats}")
        
        if self._client:
            try:
                # aiomqtt v2 handles disconnection in context manager
                pass  # Client will disconnect when exiting context
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
        
        # Clear state but preserve statistics for debugging
        self._subscriptions.clear()
        self._message_buffer.clear()
        
        logger.info("MQTT client disconnected gracefully")