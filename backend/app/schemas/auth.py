"""
Authentication schemas
"""
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class LoginResponse(BaseModel):
    """Login response schema"""
    success: bool = True
    data: dict = Field(..., description="Login data including tokens and user info")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                    "expires_in": 3600,
                    "user": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "email": "user@example.com",
                        "full_name": "John Doe",
                        "roles": ["user"],
                        "permissions": ["read:conversations", "write:conversations"]
                    }
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator('new_password')
    def validate_password_strength(cls, v, values):
        """Validate password strength"""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        
        # Check for at least one uppercase, one lowercase, one digit
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        return v


class RequestPasswordResetRequest(BaseModel):
    """Request password reset schema"""
    email: EmailStr = Field(..., description="Email address to send reset link")


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        return v


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class TwoFactorRequest(BaseModel):
    """Two-factor authentication request"""
    code: str = Field(..., regex="^[0-9]{6}$", description="6-digit 2FA code")


class TwoFactorSetupResponse(BaseModel):
    """Two-factor setup response"""
    secret: str = Field(..., description="2FA secret key")
    qr_code: str = Field(..., description="QR code image as base64")
    backup_codes: List[str] = Field(..., description="Backup codes")