from pydantic import BaseModel,Field
from datetime import datetime
from enum import Enum

class ActuatorState(str,Enum):
    ON="on"
    OFF = "off"
    ERROR = "error"

class ActuatorStatusHistory(BaseModel):
    actuator_name:str=Field(...,min_length=3,max_length=50,description="Name of the actuator")
    farm_name:str = Field(...,min=1,max=25,description="Farm name")
    modified:datetime= Field(default_factory=datetime.now,description="Timestamp when status was modified")
    status:ActuatorState= Field(...,description="Current state of the actuator")
