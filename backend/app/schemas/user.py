"""
User schemas
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID
from .common import TimestampMixin

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)
    roles: Optional[List[str]] = Field(default=["user"])
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None

class UserResponse(UserBase, TimestampMixin):
    """User response schema"""
    id: UUID
    roles: List[str]
    permissions: List[str]
    last_login: Optional[datetime] = None
    email_verified: bool = False
    two_factor_enabled: bool = False
    
    class Config:
        orm_mode = True

class UserListResponse(BaseModel):
    """User list response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "users": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@example.com",
                            "full_name": "John Doe",
                            "is_active": True,
                            "roles": ["user"],
                            "permissions": ["read:conversations"],
                            "created_at": "2024-01-01T00:00:00Z",
                            "updated_at": "2024-01-01T00:00:00Z"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "limit": 20,
                        "total": 100,
                        "pages": 5
                    }
                }
            }
        }

class RoleResponse(BaseModel):
    """Role response schema"""
    id: UUID
    name: str
    description: Optional[str] = None
    permissions: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PermissionResponse(BaseModel):
    """Permission response schema"""
    id: UUID
    name: str
    description: Optional[str] = None
    resource: str
    action: str
    
    class Config:
        orm_mode = True

class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    timezone: Optional[str] = None
    language: Optional[str] = Field(None, regex="^[a-z]{2}(-[A-Z]{2})?$")
    notification_preferences: Optional[dict] = None

class UserPreferences(BaseModel):
    """User preferences schema"""
    theme: str = Field("light", regex="^(light|dark|auto)$")
    language: str = Field("en", regex="^[a-z]{2}(-[A-Z]{2})?$")
    timezone: str = "UTC"
    notifications: dict = Field(default_factory=lambda: {
        "email": True,
        "push": True,
        "sms": False
    })
    privacy: dict = Field(default_factory=lambda: {
        "show_online_status": True,
        "show_last_seen": True,
        "profile_visibility": "public"
    })

class UserStats(BaseModel):
    """User statistics schema"""
    user_id: UUID
    total_conversations: int = 0
    total_messages: int = 0
    total_bookmarks: int = 0
    total_exports: int = 0
    storage_used_mb: float = 0.0
    last_activity: Optional[datetime] = None
    
    class Config:
        orm_mode = True