from pydantic import BaseModel, Field,field_validator
from datetime import datetime, timezone
from enum import Enum
from typing import Optional,Tuple,Any
from app.core.config import KTM_TZ

class Sensor(BaseModel):
    sensor_id:str
    value: float
    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when sensor data was created (UTC)"
    )

class DeviceType(str, Enum):
    ANALOG = "analog"
    DIGITAL = "digital"


class ResponseSensor(BaseModel):
    id:str
    sensor_name: str
    lab_id: str
    unit: str
    sensor_type: DeviceType
    range: Optional[Tuple[float, float]] = Field(
        None,
        description="(min, max) measurable values for analog sensors"
    )
    created_by: str
    created: datetime = Field(default_factory=lambda: datetime.now(KTM_TZ))

    @field_validator("range")
    @classmethod
    def validate_range(cls, value, info):
        sensor_type = info.data.get("sensor_type")  # Access other fields

        if sensor_type == DeviceType.ANALOG:
            if not value:
                raise ValueError("Analog sensors must define a range (min, max).")
            if len(value) != 2 or value[0] >= value[1]:
                raise ValueError("Range must be a tuple of (min, max) where min < max.")
        elif sensor_type == DeviceType.DIGITAL:
            return None

        return value


class RegisterSensor(BaseModel):
    sensor_name: str
    lab_id: str
    unit: str
    sensor_type: DeviceType
    created_by: str= Field(default="system", description="User who created the sensor")
    range: Optional[Tuple[float, float]] = Field(
        None,
        description="(min, max) measurable values for analog sensors"
    )
    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("range")
    @classmethod
    def validate_range(cls, value, info):
        sensor_type = info.data.get("sensor_type")  # Access other fields

        if sensor_type == DeviceType.ANALOG:
            if not value:
                raise ValueError("Analog sensors must define a range (min, max).")
            if len(value) != 2 or value[0] >= value[1]:
                raise ValueError("Range must be a tuple of (min, max) where min < max.")
        elif sensor_type == DeviceType.DIGITAL:
            return None

        return value

