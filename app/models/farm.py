from pydantic import BaseModel,Field,field_validator
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

    @field_validator("target_plant", mode="before")
    @classmethod
    def normalize_target_plant(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
            return TargetPlant(v)   
        return v


    @field_validator("preference", mode="before")
    @classmethod
    def normalize_preference(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
            return PreferenceMode(v) 
        return v