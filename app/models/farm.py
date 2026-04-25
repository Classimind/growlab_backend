from pydantic import BaseModel,Field
from datetime import datetime,timezone
from typing import Optional,List
from app.models.preference import PreferenceMode,TargetPlant
from app.core.roles import Role


class LabEmployee(BaseModel):
    user_id: str
    role: Role

class Lab(BaseModel):
    id: Optional[str] = Field(default=None)
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(default="Hydroponics optimization lab")
    target_plant: TargetPlant = Field(default=TargetPlant.LETTUCE)
    preference: PreferenceMode = Field(default=PreferenceMode.BALANCED)
    created_by: str
    employees: List[LabEmployee] = Field(default_factory=list)
    status: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )