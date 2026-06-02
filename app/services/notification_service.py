from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from firebase_admin.exceptions import FirebaseError

from app.services.firebase_service import (
    send_push_to_topic,
    send_push_to_token
)
from app.models.notification import NotificationModel
from app.db.clients import get_db

def get_notification_collection():
    db = get_db()
    return db["notifications"]


async def create_notification(
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    tokens: Optional[List[str]] = None,
    topic: Optional[str] = None,
    user_id: Optional[str] = None,
    farm_id: Optional[str] = None,
    image: Optional[str] = None,
) -> NotificationModel:

    data = data or {}
    tokens = tokens or []

    notification_collection = get_notification_collection()

    notif = NotificationModel(
        title=title,
        body=body,
        data=data,
        tokens=tokens,
        topic=topic,
        status="pending",
        user_id=user_id,
        farm_id=farm_id,
        image=image,
        created_at=datetime.now(timezone.utc),
    )

    result = await notification_collection.insert_one(
        notif.model_dump()
    )

    notif.id = str(result.inserted_id)

    return notif


async def process_pending_notifications():
    notification_collection = get_notification_collection()

    cursor = notification_collection.find(
        {"status": "pending"}
    )

    async for notif_doc in cursor:

        notif = NotificationModel(**notif_doc)

        try:
            #  SEND VIA TOPIC
            if notif.topic:
                await send_push_to_topic(
                    notif.topic,
                    notif.title,
                    notif.body,
                    notif.data
                )

            #  SEND VIA TOKENS (batch safe)
            elif notif.tokens:
                for token in notif.tokens[:20]:  # safety limit
                    await send_push_to_token(
                        token,
                        notif.title,
                        notif.body,
                        notif.data
                    )
            else:
                raise ValueError("No target (tokens/topic) specified")

            #  MARK SENT
            await notification_collection.update_one(
                {"_id": notif_doc["_id"]},
                {
                    "$set": {
                        "status": "sent",
                        "sent_at": datetime.now(timezone.utc)
                    }
                }
            )

        except FirebaseError as e:

            await notification_collection.update_one(
                {"_id": notif_doc["_id"]},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.now(timezone.utc)
                    }
                }
            )

        except Exception as e:

            await notification_collection.update_one(
                {"_id": notif_doc["_id"]},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.now(timezone.utc)
                    }
                }
            )




