from pydantic import BaseModel, Field
from datetime import datetime, timezone

class Sensor(BaseModel):
    sensor_name: str
    farm_id: str
    value: float
    unit: str | None = None
    sensor_type: str | None = None
    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when sensor data was created (UTC)"
    )
