from pydantic import BaseModel, Field, field_validator,field_serializer
from typing import List, Optional
from datetime import datetime
from app.models.farm import FarmRole


class APIKeyModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    name:str
    lab_id: str
    hashed_key: str
    permissions: List[str] = Field(..., min_length=1)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    @field_validator("permissions")
    def validate_permissions(cls, v):
        allowed = {'read', 'create', 'update', 'delete', 'manage_users'}

        for p in v:
            if p not in allowed:
                raise ValueError(f"Invalid permission: {p}")

        return v
    
    @field_serializer("created_at")
    def format_date(self, value: datetime):
        return value.strftime("%Y-%m-%d")
    
    @field_serializer("user_id", "lab_id")
    def seralized_userId(self,value):
        return str(value)


class APIKeyCreateRequest(BaseModel):
    name:str
    lab_id: str
    role: FarmRole   
    created_at: datetime = Field(default_factory=datetime.now)         
    expires_at: Optional[datetime] = None

    @field_validator("role", mode="before")
    @classmethod
    def parse_role(cls, v):
        if isinstance(v, FarmRole):
            return v
        if isinstance(v, str):
            v = v.strip().upper()
            try:
                return FarmRole[v]
            except KeyError:
                raise ValueError("Invalid role")
        raise ValueError("Invalid role type")