import asyncio
import os
import logging
import asyncio_mqtt as mqtt_async
import ssl
from ..ports.mqtt_client_port import MqttClientPort
from ..domain.exceptions import MqttAdapterError
from ..config import get_settings

logger = logging.getLogger(__name__)

class AsyncioMqttAdapter(MqttClientPort):
    def __init__(self, message_handler: callable):
        self.message_handler = message_handler
        self._client = None
        self._subscribe_topic = "test" # Define your topic here if not configurable
        self._max_retries = 5
        self._base_delay = 1

    async def connect_and_listen(self):
        settings = get_settings()

        host = settings.MQTT_HOST
        port = settings.MQTT_PORT
        username = settings.MQTT_USERNAME
        password = settings.MQTT_PASSWORD

        logger.info(f"MQTT Adapter: Attempting to connect to MQTT broker at {host}:{port}")

        client_id = f"fastapi-mqtt-adapter-{os.getpid()}"

        tls_context = None
        if settings.USE_TLS or port == 8883:
            logger.info("MQTT Adapter: Configuring TLS context.")
            try:
                tls_context = ssl.create_default_context()
                logger.info("MQTT Adapter: TLS context created successfully.")
            except ssl.SSLError as e: # Catch specific SSLError
                logger.error(f"MQTT Adapter: SSL error creating TLS context: {e}")
                # Depending on requirements, might re-raise or attempt non-TLS connection
                return
            except Exception as e:
                logger.error(f"MQTT Adapter: Unexpected error creating TLS context: {e}")
                return

        retry_count = 0
        try:
            while retry_count < self._max_retries:
                try:
                    async with mqtt_async.Client(
                        hostname=host,
                        port=port,
                        username=username,
                        password=password,
                        client_id=client_id,
                        tls_context=tls_context,
                    ) as client:
                        self._client = client
                        logger.info("MQTT Adapter: Client connected.")
                        await client.subscribe(self._subscribe_topic)
                        logger.info(f"MQTT Adapter: Subscribed to topic '{self._subscribe_topic}'")

                        async with client.messages() as messages:
                            async for message in messages:
                                logger.info(f"MQTT Adapter: Received message on topic {message.topic}")
                                # Call the injected message handler (Domain Service method)
                                # Error handling for the message handler is done within the handler itself
                                asyncio.create_task(self.message_handler(str(message.topic), message.payload.decode()))

                except mqtt_async.MqttError as e:
                    retry_count += 1
                    delay = self._base_delay * (2 ** (retry_count - 1))
                    logger.error(f"MQTT Adapter: MQTT error occurred: {e}. Attempting to reconnect in {delay} seconds. (Attempt {retry_count}/{self._max_retries})")
                    await asyncio.sleep(delay)
                except Exception as e:
                    retry_count += 1
                    delay = self._base_delay * (2 ** (retry_count - 1))
                    logger.error(f"MQTT Adapter: An unexpected error occurred in the connect loop: {e}. Attempting to reconnect in {delay} seconds. (Attempt {retry_count}/{self._max_retries})")
                    await asyncio.sleep(delay)

            logger.error(f"MQTT Adapter: Maximum number of reconnection attempts ({self._max_retries}) reached. Giving up.")
        except asyncio.CancelledError:
            logger.info("MQTT Adapter: Connect task cancelled.")
        finally:
            self._client = None
            logger.info("MQTT Adapter: Client disconnected.")

    async def publish(self, topic: str, payload: str):
        if not self._client or not self._client.is_connected():
            logger.error("MQTT Adapter: Cannot publish message to {topic}, client not connected.")
            raise MqttAdapterError("MQTT client not connected.")
        try:
            logger.info(f"MQTT Adapter: Publishing message to topic {topic}")
            await self._client.publish(topic, payload)
            logger.info(f"MQTT Adapter: Message published successfully to {topic}.")
        except mqtt_async.MqttError as e: # Catch specific MQTT error during publish
            logger.error(f"MQTT Adapter: MQTT error publishing message to {topic}: {e}")
            raise MqttAdapterError(f"Error publishing MQTT message to {topic}: {e}") from e
        except Exception as e:
            logger.error(f"MQTT Adapter: An unexpected error occurred publishing message to {topic}: {e}")
            raise MqttAdapterError(f"Unexpected error publishing MQTT message to {topic}: {e}") from e

    # Implement other methods from MqttClientPort if needed
    # async def unsubscribe(self, topic: str): ...
    # async def disconnect(self): ... 