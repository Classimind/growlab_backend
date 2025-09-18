from pydantic import BaseModel
from typing import Optional

class Plant(BaseModel):
    plant_name: str
    type: str
    ph_range: str
    ec_range: str
    light_hours: str
    growth_cycle_days: str
    notes: Optional[str] = None