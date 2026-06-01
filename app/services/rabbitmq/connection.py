import aio_pika
from app.core.config import settings


class RabbitMQConnection:
    connection: aio_pika.RobustConnection | None = None
    channel: aio_pika.Channel | None = None
    exchange: aio_pika.Exchange | None = None

    @classmethod
    async def connect(cls):
        cls.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        cls.channel = await cls.connection.channel()

        cls.exchange = await cls.channel.declare_exchange(
            "firmware",
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    @classmethod
    async def close(cls):
        if cls.connection:
            await cls.connection.close()