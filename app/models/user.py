from pydantic import BaseModel, EmailStr, Field, field_validator,model_validator
from typing import Optional,List
from enum import Enum
from typing import Dict
from datetime import datetime,timezone
import re
from app.core.roles import Role,FarmRole
from pydantic import EmailStr

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


class FCMTokenUpdate(BaseModel):
    fcm_token: str


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

class UserSecurity(BaseModel):
    is_active: bool = True
    is_verified: bool = False

    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

class UserProfile(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None


class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    # AUTH
    email: Optional[EmailStr] = None
    password: Optional[str] = None  # hashed only
    provider: Provider = Provider.EMAIL
    oauth: Optional[OAuthUser] = None

    # PROFILE
    profile: UserProfile = UserProfile()

    # AUTHZ
    role: Role = Role.USER
    # domain_ids: Dict[str, FarmRole] = Field(default_factory=dict)
    domain_ids: Dict[str, FarmRole] = Field(default_factory=dict)


    # SECURITY
    security: UserSecurity = UserSecurity()

    # SESSIONS
    sessions: List[Dict] = []

    # METADATA
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    @field_validator("domain_ids", mode="before")
    def fix_domain_ids(cls, v):
        if v is None:
            return {}
        if isinstance(v, list):
            return {} 
        return v

    class Config:
        populate_by_name = True



class OAuthLogin(BaseModel):
    provider: Provider
    provider_user_id: str
    access_token: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class Token(BaseModel):
    id: str
    access_token: str
    refresh_token:str
    token_type: str = "bearer"
    expire:str