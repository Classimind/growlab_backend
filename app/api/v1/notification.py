from fastapi import APIRouter, HTTPException, Query ,Depends
from app.db.clients import get_db
from app.services.notification_service import create_notification
from app.services.firebase_service import send_push_to_topic, send_push_to_token
from bson import ObjectId
from app.core.auth_identity import get_current_user
from app.models.notification import  NotificationRequest, NotificationResponse,NotificationListItem,NotificationListResponse
from typing import List, Optional, Dict, Any
router = APIRouter()


@router.post("/notifications", response_model=NotificationResponse)
async def create_notification_endpoint(req: NotificationRequest):


    if not req.tokens and not req.topic:
        raise HTTPException(
            status_code=400,
            detail="Either 'tokens' or 'topic' must be provided"
        )

    if req.tokens and req.topic:
        raise HTTPException(
            status_code=400,
            detail="Provide only one: 'tokens' OR 'topic'"
        )

    try:
        notif = await create_notification(
            title=req.title,
            body=req.body,
            data=req.data,
            tokens=req.tokens,
            topic=req.topic,
            user_id=req.user_id,
            farm_id=req.farm_id,
            image=req.image,
        )
        if notif.tokens:
            await send_push_to_token(notif.tokens[0], notif.title, notif.body)  # Example: send to first token
        return notif.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    user= Depends(get_current_user),
    farm_id: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),  
    read: Optional[bool] = Query(None),      
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    db = get_db()
    collection = db.notifications

    query = {}

    if user:
        query["user_id"] = user['user_id']

    if farm_id:
        query["farm_id"] = farm_id

    if device_id:
        query["deviceId"] = device_id

    if read is not None:
        query["read"] = read
    
    query["status"] = "sent"  # Only show sent notifications
    skip = (page - 1) * page_size

    total = await collection.count_documents(query)

    cursor = (
        collection.find(query)
        .sort("created_at", -1)   # newest first
        .skip(skip)
        .limit(page_size)
    )

    notifications: List[NotificationListItem] = []

    async for doc in cursor:
        notifications.append(
            NotificationListItem(
                id=str(doc["_id"]),
                title=doc.get("title", ""),
                body=doc.get("body", ""),
                image=doc.get("image"),
                status=doc.get("status", "unknown"),
                created_at=doc.get("created_at"),
                read=doc.get("read", False),
            )
        )

    return NotificationListResponse(
        notifications=notifications,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/notifications/{notification_id}/read")
async def mark_as_read(notification_id: str, user=Depends(get_current_user)):
    db = get_db()
    collection = db.notifications

    result = await collection.update_one(
        {"_id": ObjectId(notification_id), "user_id": user['user_id']},
        {"$set": {"read": True}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"status": "success"}


@router.patch("/notifications/read-all")
async def mark_all_as_read(
    farm_id: Optional[str] = None,
    user=Depends(get_current_user)
):
    db = get_db()
    collection = db.notifications

    query = {}

    if farm_id:
        query["farm_id"] = farm_id

    if user:
        query["user_id"] = user['user_id']

    await collection.update_many(
        query,
        {"$set": {"read": True}}
    )

    return {"status": "all marked as read"}