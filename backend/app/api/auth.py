"""
Authentication API endpoints
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.models.user import User
from app.models.audit import AuditLog, AuditAction
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    verify_token,
    verify_password,
    get_password_hash
)
from app.core.auth import get_current_user

router = APIRouter()
security = HTTPBearer()


# Request/Response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool = True
    data: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    roles: list[str]
    permissions: list[str]


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    """
    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == request.email,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(request.password, user.password_hash):
        # Log failed login attempt
        if user:
            audit_log = AuditLog(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                resource_type="user",
                resource_id=user.id,
                metadata={"reason": "invalid_password"}
            )
            db.add(audit_log)
            await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={
            "email": user.email,
            "roles": [role.name for role in user.roles]
        }
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Log successful login
    audit_log = AuditLog(
        user_id=user.id,
        action=AuditAction.LOGIN,
        resource_type="user",
        resource_id=user.id
    )
    db.add(audit_log)
    await db.commit()
    
    # Prepare response
    return LoginResponse(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600,  # 1 hour
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "roles": [role.name for role in user.roles],
                "permissions": user.get_permissions()
            }
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={
            "email": user.email,
            "roles": [role.name for role in user.roles]
        }
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=3600
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout and invalidate tokens
    """
    # Log logout
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.LOGOUT,
        resource_type="user",
        resource_id=current_user.id
    )
    db.add(audit_log)
    await db.commit()
    
    # TODO: Add token to blacklist in Redis
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        roles=[role.name for role in current_user.roles],
        permissions=current_user.get_permissions()
    )


@router.post("/change-password")
async def change_password(
    current_password: str = Body(...),
    new_password: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password
    """
    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(new_password)
    
    # Log password change
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.PASSWORD_CHANGED,
        resource_type="user",
        resource_id=current_user.id
    )
    db.add(audit_log)
    await db.commit()
    
    return {"success": True, "message": "Password changed successfully"}


@router.post("/request-password-reset")
async def request_password_reset(
    email: EmailStr = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email
    """
    # Find user by email
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.is_active == True,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration
    if user:
        # TODO: Generate reset token and send email
        pass
    
    return {
        "success": True, 
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post("/reset-password")
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using token
    """
    # TODO: Implement password reset with token verification
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not implemented yet"
    )