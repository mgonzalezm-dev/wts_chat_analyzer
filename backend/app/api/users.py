"""
Users API endpoints
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db.session import get_db
from app.models.user import User, Role
from app.models.audit import AuditLog, AuditAction
from app.core.auth import get_current_active_user, require_permission
from app.core.security import get_password_hash
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserProfileUpdate,
    UserPreferences,
    UserStats
)

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin only)
    """
    # Build query
    query = select(User).where(User.deleted_at.is_(None))
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    if role:
        query = query.join(User.roles).where(Role.name == role)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    query = query.order_by(User.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Format response
    return UserListResponse(
        data={
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "roles": [role.name for role in user.roles],
                    "permissions": user.get_permissions(),
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "last_login": user.last_login
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("users:create")),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new user (admin only)
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=get_password_hash(user_data.password),
        is_active=user_data.is_active
    )
    
    # Assign roles
    if user_data.roles:
        result = await db.execute(
            select(Role).where(Role.name.in_(user_data.roles))
        )
        roles = result.scalars().all()
        user.roles = roles
    
    db.add(user)
    
    # Log user creation
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.USER_CREATED,
        resource_type="user",
        resource_id=user.id,
        metadata={"email": user.email}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
        permissions=user.get_permissions(),
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user details
    """
    # Users can view their own profile, admins can view any
    if str(user_id) != str(current_user.id) and not current_user.has_permission("users:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
        permissions=user.get_permissions(),
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login,
        email_verified=user.email_verified,
        two_factor_enabled=user.two_factor_enabled
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission("users:update")),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user (admin only)
    """
    # Get user
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    
    if "email" in update_data:
        # Check if new email already exists
        result = await db.execute(
            select(User).where(
                User.email == update_data["email"],
                User.id != user_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = update_data["email"]
        user.email_verified = False  # Reset verification
    
    if "full_name" in update_data:
        user.full_name = update_data["full_name"]
    
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]
    
    if "roles" in update_data:
        result = await db.execute(
            select(Role).where(Role.name.in_(update_data["roles"]))
        )
        roles = result.scalars().all()
        user.roles = roles
    
    # Log update
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.USER_UPDATED,
        resource_type="user",
        resource_id=user.id,
        metadata={"changes": list(update_data.keys())}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
        permissions=user.get_permissions(),
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("users:delete")),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (soft delete, admin only)
    """
    # Prevent self-deletion
    if str(user_id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete
    from datetime import datetime
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    
    # Log deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.USER_DELETED,
        resource_type="user",
        resource_id=user.id
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"success": True, "message": "User deleted successfully"}


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user statistics
    """
    # Users can view their own stats, admins can view any
    if str(user_id) != str(current_user.id) and not current_user.has_permission("users:read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these statistics"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate statistics
    from app.models.conversation import Conversation
    from app.models.bookmark import Bookmark
    from app.models.export import Export
    
    # Count conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.owner_id == user_id,
            Conversation.deleted_at.is_(None)
        )
    )
    total_conversations = conv_result.scalar() or 0
    
    # Count messages
    msg_result = await db.execute(
        select(func.sum(Conversation.message_count)).where(
            Conversation.owner_id == user_id,
            Conversation.deleted_at.is_(None)
        )
    )
    total_messages = msg_result.scalar() or 0
    
    # Count bookmarks
    bookmark_result = await db.execute(
        select(func.count(Bookmark.id)).where(
            Bookmark.user_id == user_id,
            Bookmark.deleted_at.is_(None)
        )
    )
    total_bookmarks = bookmark_result.scalar() or 0
    
    # Count exports
    export_result = await db.execute(
        select(func.count(Export.id)).where(
            Export.user_id == user_id,
            Export.deleted_at.is_(None)
        )
    )
    total_exports = export_result.scalar() or 0
    
    # Calculate storage
    storage_result = await db.execute(
        select(func.sum(Conversation.file_size)).where(
            Conversation.owner_id == user_id,
            Conversation.deleted_at.is_(None)
        )
    )
    storage_bytes = storage_result.scalar() or 0
    storage_mb = storage_bytes / (1024 * 1024)
    
    return UserStats(
        user_id=user_id,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_bookmarks=total_bookmarks,
        total_exports=total_exports,
        storage_used_mb=round(storage_mb, 2),
        last_activity=user.last_login
    )


@router.put("/profile/update", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile
    """
    # Update profile fields
    update_data = profile_data.dict(exclude_unset=True)
    
    if "full_name" in update_data:
        current_user.full_name = update_data["full_name"]
    
    if "phone" in update_data:
        current_user.metadata = current_user.metadata or {}
        current_user.metadata["phone"] = update_data["phone"]
    
    if "timezone" in update_data:
        current_user.metadata = current_user.metadata or {}
        current_user.metadata["timezone"] = update_data["timezone"]
    
    if "language" in update_data:
        current_user.metadata = current_user.metadata or {}
        current_user.metadata["language"] = update_data["language"]
    
    if "notification_preferences" in update_data:
        current_user.metadata = current_user.metadata or {}
        current_user.metadata["notification_preferences"] = update_data["notification_preferences"]
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        roles=[role.name for role in current_user.roles],
        permissions=current_user.get_permissions(),
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
        email_verified=current_user.email_verified,
        two_factor_enabled=current_user.two_factor_enabled
    )


@router.get("/profile/preferences", response_model=UserPreferences)
async def get_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's preferences
    """
    metadata = current_user.metadata or {}
    
    return UserPreferences(
        theme=metadata.get("theme", "light"),
        language=metadata.get("language", "en"),
        timezone=metadata.get("timezone", "UTC"),
        notifications=metadata.get("notification_preferences", {
            "email": True,
            "push": True,
            "sms": False
        }),
        privacy=metadata.get("privacy_settings", {
            "show_online_status": True,
            "show_last_seen": True,
            "profile_visibility": "public"
        })
    )


@router.put("/profile/preferences", response_model=UserPreferences)
async def update_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's preferences
    """
    current_user.metadata = current_user.metadata or {}
    
    current_user.metadata.update({
        "theme": preferences.theme,
        "language": preferences.language,
        "timezone": preferences.timezone,
        "notification_preferences": preferences.notifications,
        "privacy_settings": preferences.privacy
    })
    
    await db.commit()
    
    return preferences