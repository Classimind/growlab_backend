import json
import aio_pika

from ..services.rabbitmq.connection import RabbitMQConnection


class PublisherService:

    @staticmethod
    async def publish_update(device: str, version: int):

        exchange = RabbitMQConnection.exchange

        if not exchange:
            raise RuntimeError("RabbitMQ not initialized")

        message = {
            "event": "firmware_update",
            "device": device,
            "version": version,
        }

        msg = aio_pika.Message(
            body=json.dumps(message).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await exchange.publish(
            msg,
            routing_key=f"firmware.{device}",
        )