from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime



class NotificationStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"


class NotificationModel(BaseModel):
    # Identity
    id: Optional[str] = None

    # Content
    title: str
    body: str
    image: Optional[str] = None
    data: Dict = Field(default_factory=dict)

    # Targeting
    tokens: List[str] = Field(default_factory=list)
    topic: Optional[str] = None
    user_id: Optional[str] = None
    farm_id: Optional[str] = None

    # Status & lifecycle
    status: NotificationStatus = NotificationStatus.PENDING

    # Scheduling
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None

    # Delivery tracking
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None

    # Retry system
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None

    # Provider response
    fcm_response: Optional[Dict] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None





class NotificationRequest(BaseModel):
    title: str
    body: str
    image: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    tokens: Optional[List[str]] = None
    topic: Optional[str] = None

    user_id: Optional[str] = None
    farm_id: Optional[str] = None


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    image: Optional[str]
    data: Dict[str, Any]
    tokens: List[str]
    topic: Optional[str]
    status: str
    created_at: datetime


class NotificationListItem(BaseModel):
    id: str
    title: str
    body: str
    image: Optional[str]
    status: str
    created_at: datetime
    read: bool = False


class NotificationListResponse(BaseModel):
    notifications: List[NotificationListItem]
    total: int
    page: int
    page_size: int