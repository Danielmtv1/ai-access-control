import asyncio
import aiomqtt
from typing import Optional, Callable, Dict, Any
import logging
from app.infrastructure.observability.metrics import mqtt_connection_status
from app.config import get_settings

logger = logging.getLogger(__name__)

class MqttClient:
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[aiomqtt.Client] = None
        self.connected = False
        self.reconnect_delay = 1  # Start with a smaller delay
        self.max_reconnect_delay = 60
        self._message_handlers: Dict[str, Callable] = {}
        self._running = False
        self._message_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Conectar al broker MQTT"""
        try:
            # Use async with for reliable connection management
            self.client = aiomqtt.Client(
                hostname=self.settings.MQTT_HOST,
                port=self.settings.MQTT_PORT,
                username=self.settings.MQTT_USERNAME,
                password=self.settings.MQTT_PASSWORD,
                keepalive=60,
            )
            
            # The actual connection happens when entering the async with block
            # We don't call connect() here directly anymore
            logger.info(f"Attempting to connect to MQTT broker at {self.settings.MQTT_HOST}:{self.settings.MQTT_PORT}")
            
            # The message processing loop will handle the connection and messages
            # We set connected to False initially and update it in the loop
            self.connected = False
            mqtt_connection_status.set(1)
            
        except Exception as e:
            self.connected = False
            mqtt_connection_status.set(0)
            logger.error(f"❌ Error during MQTT client initialization: {str(e)}")
            # Do not re-raise here, let the reconnection logic handle it

    async def disconnect(self):
        """Desconectar del broker MQTT"""
        # Disconnection is handled implicitly when exiting the async with block
        # in _run_client
        pass # No explicit disconnect needed with async with

    async def subscribe(self, topic: str, handler: Callable):
        """Suscribirse a un tópico"""
        if not self.connected or not self.client:
             logger.warning(f"Cannot subscribe to {topic}: MQTT client not connected")
             # Store handlers even if not connected, resubscribe on connect
             self._message_handlers[topic] = handler
             return
            
        try:
            await self.client.subscribe(topic)
            self._message_handlers[topic] = handler
            logger.info(f"Suscrito al tópico: {topic}")
        except Exception as e:
            logger.error(f"Error suscribiéndose al tópico {topic}: {str(e)}")
            # Do not re-raise here

    async def publish(self, topic: str, message: str):
        """Publicar mensaje en un tópico"""
        if not self.connected or not self.client:
            logger.warning(f"Cannot publish to {topic}: MQTT client not connected")
            return
            
        try:
            await self.client.publish(topic, message)
            logger.debug(f"Mensaje publicado en {topic}: {message}")
        except Exception as e:
            logger.error(f"Error publicando en {topic}: {str(e)}")
            # Do not re-raise here

    async def _process_message(self, message: aiomqtt.Message):
        """Procesar un mensaje individual"""
        topic = message.topic.value
        if topic in self._message_handlers:
            try:
                await self._message_handlers[topic](message)
            except Exception as e:
                logger.error(f"Error procesando mensaje de {topic}: {str(e)}")

    async def _run_client(self):
        """Corre el cliente MQTT y maneja mensajes y reconexión"""
        while self._running:
            try:
                # The async with block manages connection and disconnection
                async with self.client:
                    self.connected = True
                    mqtt_connection_status.set(1)
                    logger.info("✅ MQTT client connected and listening")
                    
                    # Resuscribe on successful connection
                    for topic, handler in self._message_handlers.items():
                         await self.subscribe(topic, handler) # Use internal subscribe

                    # Process messages in a loop
                    async for message in self.client.messages:
                        await self._process_message(message)

            except aiomqtt.MqttError as e:
                self.connected = False
                mqtt_connection_status.set(0)
                logger.error(f"❌ MQTT error: {str(e)}. Attempting to reconnect...")
                # The while loop will continue and attempt reconnection

            except asyncio.CancelledError:
                 logger.info("MQTT client task cancelled")
                 self.connected = False
                 mqtt_connection_status.set(0)
                 break # Exit while loop on cancellation

            except Exception as e:
                self.connected = False
                mqtt_connection_status.set(0)
                logger.error(f"❌ Unexpected error in MQTT client: {str(e)}. Attempting to reconnect...")
                # The while loop will continue and attempt reconnection

            # Wait before attempting to reconnect
            if self._running:
                 logger.info(f"Waiting {self.reconnect_delay} seconds before next reconnect attempt")
                 await asyncio.sleep(self.reconnect_delay)
                 # Increase delay exponentially
                 self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    async def start(self):
        """Iniciar el cliente MQTT"""
        if not self._running:
            self._running = True
            await self.connect() # Initialize client instance
            self._message_task = asyncio.create_task(
                self._run_client(),
                name="mqtt_run_client_task"
            )
            logger.info("MQTT client start task created")

    async def stop(self):
        """Detener el cliente MQTT"""
        if self._running:
            logger.info("Stopping MQTT client...")
            self._running = False
            if self._message_task:
                self._message_task.cancel()
                try:
                    await self._message_task
                except asyncio.CancelledError:
                    pass # Task was cancelled as intended
                except Exception as e:
                    logger.error(f"Error waiting for MQTT client task to finish: {str(e)}")
            
            # Ensure client is properly closed if async with wasn't fully exited
            if self.client and hasattr(self.client, '__aexit__'):
                 try:
                     await self.client.__aexit__(None, None, None)
                 except Exception as e:
                     logger.error(f"Error during MQTT client __aexit__: {str(e)}")

            self.client = None
            self.connected = False
            mqtt_connection_status.set(0)
            logger.info("MQTT client stopped") 