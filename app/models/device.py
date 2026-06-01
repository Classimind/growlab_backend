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
    current_version: str = Field(..., description="Current firmware version")



class DeviceStatusOut(BaseModel):
    deviceId: str
    farmId: str

    status: str
    bootCount: int
    uptime: int
    current_version: str                                 
    ip: Optional[str] = None

    last_seen: datetime
    is_online: bool = False


class OTAUpdateResult(BaseModel):
    device_id: str
    from_version: str
    to_version: str
    success: bool
    error_message: Optional[str] = None

class OTAManifestRequest(BaseModel):
    device_id: str
    current_version: str
    device_type: str = "esp32"