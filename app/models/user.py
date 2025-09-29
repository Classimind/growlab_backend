from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from enum import Enum
from typing import Dict
from datetime import datetime,timezone

class Provider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    GITHUB = "github"

from enum import Enum

class Role(str, Enum):
    # Company roles
    COMPANY_SUPERADMIN = "growlab:superadmin"
    COMPANY_EMPLOYEE = "growlab:employee"

    # Farm roles
    FARM_ADMIN = "farm:admin"
    FARM_EMPLOYEE = "farm:employee"

    # Normal role
    USER = "user"


class OAuthUser(BaseModel):
    provider: Provider = Field(..., description="OAuth provider")
    provider_user_id: str = Field(..., description="Unique ID from the OAuth provider")
    email: Optional[EmailStr] = Field(None, description="User email from provider")
    name: Optional[str] = Field(None, description="User full name")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar")
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")

class User(BaseModel):
    email: Optional[EmailStr] = Field(None, description="User email (required if provider is EMAIL)")
    password: Optional[str] = Field(None, description="User password (required if provider is EMAIL)")
    provider: Provider = Field(..., description="Authentication provider")
    oauth: Optional[OAuthUser] = Field(None, description="OAuth details if provider is not EMAIL")
    created_at:datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    role: Role = Role.USER
    domain_ids: Dict[str, Role] = Field(default_factory=dict, description="Mapping of domain_id → role")

    # -------------------------
    # Validators
    # -------------------------
    @field_validator("email", "password", mode="before")
    @classmethod
    def validate_email_password(cls, v, info):
        if info.data.get("provider") == Provider.EMAIL and v is None:
            raise ValueError(f"{info.field.name} is required for email authentication")
        return v

    @field_validator("oauth", mode="before")
    @classmethod
    def validate_oauth(cls, v, info):
        if info.data.get("provider") != Provider.EMAIL and v is None:
            raise ValueError("OAuth details are required for non-email providers")
        return v

class EmailSignup(BaseModel):
    email: EmailStr
    password: str

class EmailLogin(BaseModel):
    email: EmailStr
    password: str

class OAuthLogin(BaseModel):
    provider: Provider
    provider_user_id: str
    access_token: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token:str
    token_type: str = "bearer"