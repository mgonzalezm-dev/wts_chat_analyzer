"""
Authentication dependencies and decorators
"""

from typing import Optional, List, Callable
from functools import wraps
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_token
from app.models.audit import AuditLog, AuditAction

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: Bearer token from request header
        db: Database session
    
    Returns:
        Current user object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (not deleted or deactivated)
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current active user
    
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    if current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Deleted user"
        )
    
    return current_user


def require_permission(resource: str, action: str):
    """
    Dependency to require specific permission
    
    Args:
        resource: Resource name (e.g., "conversations")
        action: Action name (e.g., "read", "write", "delete")
    
    Returns:
        Dependency function that checks permission
    
    Usage:
        @app.get("/admin/users", dependencies=[Depends(require_permission("users", "read"))])
        async def get_users():
            ...
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        if not current_user.has_permission(resource, action):
            # Log permission denied
            audit_log = AuditLog(
                user_id=current_user.id,
                action=AuditAction.PERMISSION_DENIED,
                resource_type=resource,
                metadata={
                    "required_permission": f"{resource}:{action}",
                    "user_permissions": current_user.get_permissions()
                }
            )
            db.add(audit_log)
            await db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource}:{action}"
            )
        return current_user
    
    return permission_checker


def require_role(role_name: str):
    """
    Dependency to require specific role
    
    Args:
        role_name: Required role name (e.g., "admin", "analyst")
    
    Returns:
        Dependency function that checks role
    
    Usage:
        @app.get("/admin/dashboard", dependencies=[Depends(require_role("admin"))])
        async def admin_dashboard():
            ...
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        if not current_user.has_role(role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}"
            )
        return current_user
    
    return role_checker


def require_any_permission(permissions: List[tuple[str, str]]):
    """
    Dependency to require any of the specified permissions
    
    Args:
        permissions: List of (resource, action) tuples
    
    Returns:
        Dependency function that checks if user has any of the permissions
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        for resource, action in permissions:
            if current_user.has_permission(resource, action):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these permissions required: {permissions}"
        )
    
    return permission_checker


def require_all_permissions(permissions: List[tuple[str, str]]):
    """
    Dependency to require all of the specified permissions
    
    Args:
        permissions: List of (resource, action) tuples
    
    Returns:
        Dependency function that checks if user has all permissions
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ):
        for resource, action in permissions:
            if not current_user.has_permission(resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"All permissions required: {permissions}"
                )
        return current_user
    
    return permission_checker


class PermissionChecker:
    """
    Class-based permission checker for more complex scenarios
    """
    
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.has_permission(self.resource, self.action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.resource}:{self.action}"
            )
        return current_user


# Convenience permission checkers
ReadConversations = PermissionChecker("conversations", "read")
WriteConversations = PermissionChecker("conversations", "write")
DeleteConversations = PermissionChecker("conversations", "delete")

ReadUsers = PermissionChecker("users", "read")
WriteUsers = PermissionChecker("users", "write")
DeleteUsers = PermissionChecker("users", "delete")

ReadAnalytics = PermissionChecker("analytics", "read")
WriteAnalytics = PermissionChecker("analytics", "write")

ExportData = PermissionChecker("exports", "create")