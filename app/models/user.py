from pydantic import BaseModel, EmailStr, Field, field_validator,model_validator
from typing import Optional
from enum import Enum
from typing import Dict
from datetime import datetime,timezone
import re
from app.core.roles import Role,FarmRole

class Provider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    GITHUB = "github"


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthUser(BaseModel):
    provider: Provider = Field(..., description="OAuth provider")
    provider_user_id: str = Field(..., description="Unique ID from the OAuth provider")
    email: Optional[EmailStr] = Field(None, description="User email from provider")
    name: Optional[str] = Field(None, description="User full name")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar")
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")

class User(BaseModel):

    email: Optional[EmailStr] = None
    password: Optional[str] = None
    provider: Provider=Provider.EMAIL
    oauth: Optional[OAuthUser] = None


    full_name: Optional[str] = Field(default=None, max_length=100)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    avatar_url: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=300)
    phone_number: Optional[str] = None
    location: Optional[str] = None

    #  GLOBAL ROLE
    role: Role = Role.USER

    #  FARM RBAC (MULTI-TENANT)
    domain_ids: Dict[str, FarmRole] = Field(
        default_factory=dict,
        description="farm_id → FarmRole mapping"
    )


    #  ACCOUNT STATUS
    is_active: bool = True
    is_verified: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    # SECURITY
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    # VALIDATION
    @model_validator(mode="after")
    def validate_auth(self):

        if self.provider == Provider.EMAIL:
            if not self.email or not self.password:
                raise ValueError("EMAIL provider requires email + password")

        else:
            if not self.oauth:
                raise ValueError("OAuth data required for non-email provider")

        return self
    


class EmailSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    # Basic profile
    full_name: Optional[str] = Field(default=None, max_length=100)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    
    # Role (restricted)
    role: Role = Role.USER

    # Legal / compliance
    accept_terms: bool

    #  Password strength validation
    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v

    #  Terms must be accepted
    @field_validator("accept_terms")
    def validate_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v

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
    expire:str