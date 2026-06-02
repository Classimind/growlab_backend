import asyncio
from concurrent.futures import ThreadPoolExecutor
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

executor = ThreadPoolExecutor(max_workers=5)

async def send_push_to_token(token: str, title: str, body: str, data: dict[str, str] | None = None) -> str:
    loop = asyncio.get_running_loop()
    try:
        message_id = await loop.run_in_executor(
            executor,
            _sync_send_to_token,
            token, title, body, data or {}
        )
        # logger.info("Sent push to token: %s...", token[:12])
        return message_id
    except FirebaseError:
        # logger.error("Firebase error sending to token", exc_info=True)
        raise
    except Exception:
        # logger.exception("Unexpected error sending to token")
        raise

def _sync_send_to_token(token: str, title: str, body: str, data: dict) -> str:
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        token=token,
    )
    return messaging.send(message)

async def send_push_to_topic(topic: str, title: str, body: str, image: str | None = None) -> str:
    loop = asyncio.get_running_loop()
    try:
        message_id = await loop.run_in_executor(
            executor,
            _sync_send_to_topic,
            topic, title, body
        )
        # logger.info("Sent push to topic: %s", topic)
        return message_id
    except FirebaseError:
        # logger.error("Firebase error sending to topic", exc_info=True)
        raise
    except Exception:
        # logger.exception("Unexpected error sending to topic")
        raise

def _sync_send_to_topic(topic: str, title: str, body: str,image: str | None = None) -> str:
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body,image=image),
        topic=topic,
    )
    return messaging.send(message)

async def subscribe_tokens_to_topic(tokens: list[str], topic: str,image: str | None = None) -> messaging.TopicManagementResponse:
    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(
            executor,
            messaging.subscribe_to_topic,
            tokens, topic,image
        )
        # logger.info("Subscribed %d tokens to topic %s", len(tokens), topic)
        return response
    except FirebaseError:
        # logger.error("Firebase error subscribing tokens", exc_info=True)
        raise
    except Exception:
        # logger.exception("Unexpected error subscribing tokens")
        raise


def _sync_send_multicast(tokens: list[str], title: str, body: str, data: dict,image: str | None = None) -> messaging.BatchResponse:
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body,image=image),
        data=data,
        tokens=tokens,
    )
    return messaging.send_each_for_multicast(message)

async def send_push_multicast(tokens: list[str], title: str, body: str, data: dict, image: str | None = None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _sync_send_multicast, tokens, title, body, data, image)
