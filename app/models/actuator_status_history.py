from pydantic import BaseModel,Field
from datetime import datetime
from enum import Enum

class ActuatorState(str,Enum):
    ON="on"
    OFF = "off"
    ERROR = "error"

class ActuatorStatusHistory(BaseModel):
    actuator_name:str
    farm_name:str
    modified:datetime= Field(default_factory=datetime.now,description="Timestamp when status was modified")
    status:ActuatorState
