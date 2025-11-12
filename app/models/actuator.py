from pydantic import BaseModel,Field,field_validator
from enum import Enum
from app.models.sensors import DeviceType
from datetime import datetime,timezone
from typing import Tuple,Optional,Union
from bson import ObjectId

class ActuatorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAULTY = "faulty"

class Actuator(BaseModel):
    actuator_name: str = Field(...)
    farmId: str = Field(...)
    actuator_type: DeviceType = Field(...)
    range: Optional[Tuple[float, float]] = Field(
        None, description="(min, max) operational values for the actuator"
    )
    unit: Optional[str] = Field(None, description="Measurement or control unit (%, °C, etc.)")
    status: ActuatorStatus = Field(
        default=ActuatorStatus.INACTIVE,
        description="Current status of the actuator"
    )
    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when actuator record was created (UTC)"
    )

    @field_validator("range")
    @classmethod
    def validate_range(cls, value, info):
        sensor_type = info.data.get("actuator_type") 
        if sensor_type == DeviceType.ANALOG:
            if not value:
                raise ValueError("Analog actuators must define a range (min, max).")
            if len(value) != 2 or value[0] >= value[1]:
                raise ValueError("Range must be a tuple of (min, max) where min < max.")
        elif sensor_type == DeviceType.DIGITAL:
            return None

        return value

class ResponseActuator(Actuator, BaseModel):
    id: str = Field(alias="_id")

    class Config:
        
        json_encoders = {
            ObjectId: str 
        }

    @classmethod
    def from_mongo(cls, doc: dict):

        if "_id" in doc:
            doc["_id"] = str(doc["_id"])   

        return cls(**doc)


class ActuatorStatus(BaseModel):
    actuator_id:str 
    value:Union[str, float, int]
    created: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when actuator record was created (UTC)"
    )

class ResponseActuatorStatus(ActuatorStatus,BaseModel):
    
    id:str = Field(alias='_id')
    class Config:
        json_encoders = {
            ObjectId: str 
        }
    @classmethod
    def from_mongo(cls,doc:dict):
        if "_id" in doc:
            doc["_id"] =str(doc["_id"])
        return cls(**doc)


