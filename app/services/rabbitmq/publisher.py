import json
import aio_pika
from .connection import RabbitMQConnection


class FirmwarePublisher:

    @staticmethod
    async def publish_update(device: str, version: int):
        exchange = RabbitMQConnection.exchange

        if exchange is None:
            raise RuntimeError("RabbitMQ not initialized")

        payload = {
            "event": "firmware_update",
            "device": device,
            "version": version,
        }

        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await exchange.publish(
            message,
            routing_key=f"firmware.{device}",
        )