from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal



class DeviceStatusIn(BaseModel):
    deviceId: str = Field(..., description="Unique ESP32 hardware ID (MAC address)")
    farmId: str = Field(..., description="Farm identifier")

    status: Literal["ON"] = Field(..., description="Device status")

    bootCount: int = Field(..., ge=0)
    uptime: int = Field(..., ge=0)

    ip: Optional[str] = None



class DeviceStatusOut(BaseModel):
    deviceId: str
    farmId: str

    status: str
    bootCount: int
    uptime: int

    ip: Optional[str] = None

    last_seen: datetime
    is_online: bool = False