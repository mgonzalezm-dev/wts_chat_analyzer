"""
Bookmarks API endpoints
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.bookmark import Bookmark
from app.models.audit import AuditLog, AuditAction
from app.core.auth import get_current_active_user
from app.schemas.bookmark import (
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    BookmarkListResponse,
    BookmarkExportRequest
)

router = APIRouter()


@router.get("/", response_model=BookmarkListResponse)
async def list_bookmarks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    conversation_id: Optional[uuid.UUID] = None,
    tags: Optional[List[str]] = Query(None),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    color: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's bookmarks with filtering
    """
    # Build query
    query = select(Bookmark).where(
        Bookmark.user_id == current_user.id,
        Bookmark.deleted_at.is_(None)
    )
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                Bookmark.title.ilike(f"%{search}%"),
                Bookmark.description.ilike(f"%{search}%")
            )
        )
    
    if conversation_id:
        query = query.where(Bookmark.conversation_id == conversation_id)
    
    if tags:
        # Filter bookmarks that have any of the specified tags
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(Bookmark.tags.contains([tag]))
        query = query.where(or_(*tag_conditions))
    
    if date_from:
        query = query.where(Bookmark.created_at >= date_from)
    
    if date_to:
        query = query.where(Bookmark.created_at <= date_to)
    
    if color:
        query = query.where(Bookmark.color == color)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.offset((page - 1) * limit).limit(limit)
    query = query.order_by(Bookmark.created_at.desc())
    
    # Execute query with message info
    query = query.options(
        selectinload(Bookmark.message).selectinload(Message.participant),
        selectinload(Bookmark.conversation)
    )
    result = await db.execute(query)
    bookmarks = result.scalars().all()
    
    # Format response
    return BookmarkListResponse(
        data={
            "bookmarks": [
                {
                    "id": str(bookmark.id),
                    "title": bookmark.title,
                    "description": bookmark.description,
                    "color": bookmark.color,
                    "tags": bookmark.tags or [],
                    "conversation_id": str(bookmark.conversation_id),
                    "message_id": str(bookmark.message_id),
                    "message_content": bookmark.message.content[:200] + "..." 
                        if len(bookmark.message.content) > 200 else bookmark.message.content,
                    "message_timestamp": bookmark.message.timestamp,
                    "sender_name": bookmark.message.participant.display_name,
                    "sender_phone": bookmark.message.participant.phone_number,
                    "created_at": bookmark.created_at,
                    "updated_at": bookmark.updated_at
                }
                for bookmark in bookmarks
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )


@router.post("/", response_model=BookmarkResponse)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new bookmark
    """
    # Verify message exists and user has access
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            Message.id == bookmark_data.message_id,
            Conversation.owner_id == current_user.id,
            Message.deleted_at.is_(None)
        )
        .options(
            selectinload(Message.participant),
            selectinload(Message.conversation)
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied"
        )
    
    # Check if bookmark already exists
    existing = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.message_id == bookmark_data.message_id,
            Bookmark.deleted_at.is_(None)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookmark already exists for this message"
        )
    
    # Create bookmark
    bookmark = Bookmark(
        user_id=current_user.id,
        conversation_id=message.conversation_id,
        message_id=message.id,
        title=bookmark_data.title,
        description=bookmark_data.description,
        color=bookmark_data.color,
        tags=bookmark_data.tags or []
    )
    db.add(bookmark)
    
    # Log bookmark creation
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKMARK_CREATED,
        resource_type="bookmark",
        resource_id=bookmark.id,
        metadata={"message_id": str(message.id)}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(bookmark)
    
    return BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        conversation_id=bookmark.conversation_id,
        message_id=bookmark.message_id,
        title=bookmark.title,
        description=bookmark.description,
        color=bookmark.color,
        tags=bookmark.tags,
        message_content=message.content,
        message_timestamp=message.timestamp,
        sender_name=message.participant.display_name,
        sender_phone=message.participant.phone_number,
        created_at=bookmark.created_at,
        updated_at=bookmark.updated_at
    )


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get bookmark details
    """
    # Get bookmark with message info
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == current_user.id,
            Bookmark.deleted_at.is_(None)
        ).options(
            selectinload(Bookmark.message).selectinload(Message.participant),
            selectinload(Bookmark.conversation)
        )
    )
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    return BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        conversation_id=bookmark.conversation_id,
        message_id=bookmark.message_id,
        title=bookmark.title,
        description=bookmark.description,
        color=bookmark.color,
        tags=bookmark.tags,
        message_content=bookmark.message.content,
        message_timestamp=bookmark.message.timestamp,
        sender_name=bookmark.message.participant.display_name,
        sender_phone=bookmark.message.participant.phone_number,
        created_at=bookmark.created_at,
        updated_at=bookmark.updated_at
    )


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: uuid.UUID,
    bookmark_data: BookmarkUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update bookmark
    """
    # Get bookmark
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == current_user.id,
            Bookmark.deleted_at.is_(None)
        ).options(
            selectinload(Bookmark.message).selectinload(Message.participant)
        )
    )
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    # Update fields
    update_data = bookmark_data.dict(exclude_unset=True)
    
    if "title" in update_data:
        bookmark.title = update_data["title"]
    
    if "description" in update_data:
        bookmark.description = update_data["description"]
    
    if "color" in update_data:
        bookmark.color = update_data["color"]
    
    if "tags" in update_data:
        bookmark.tags = update_data["tags"]
    
    bookmark.updated_at = datetime.utcnow()
    
    # Log update
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKMARK_UPDATED,
        resource_type="bookmark",
        resource_id=bookmark.id,
        metadata={"changes": list(update_data.keys())}
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(bookmark)
    
    return BookmarkResponse(
        id=bookmark.id,
        user_id=bookmark.user_id,
        conversation_id=bookmark.conversation_id,
        message_id=bookmark.message_id,
        title=bookmark.title,
        description=bookmark.description,
        color=bookmark.color,
        tags=bookmark.tags,
        message_content=bookmark.message.content,
        message_timestamp=bookmark.message.timestamp,
        sender_name=bookmark.message.participant.display_name,
        sender_phone=bookmark.message.participant.phone_number,
        created_at=bookmark.created_at,
        updated_at=bookmark.updated_at
    )


@router.delete("/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete bookmark (soft delete)
    """
    # Get bookmark
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.id == bookmark_id,
            Bookmark.user_id == current_user.id,
            Bookmark.deleted_at.is_(None)
        )
    )
    bookmark = result.scalar_one_or_none()
    
    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    # Soft delete
    bookmark.deleted_at = datetime.utcnow()
    
    # Log deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKMARK_DELETED,
        resource_type="bookmark",
        resource_id=bookmark.id
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"success": True, "message": "Bookmark deleted successfully"}


@router.post("/export")
async def export_bookmarks(
    export_request: BookmarkExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Export bookmarks to file
    """
    # Build query for bookmarks to export
    query = select(Bookmark).where(
        Bookmark.user_id == current_user.id,
        Bookmark.deleted_at.is_(None)
    )
    
    if export_request.bookmark_ids:
        query = query.where(Bookmark.id.in_(export_request.bookmark_ids))
    
    # Get bookmarks with full data
    query = query.options(
        selectinload(Bookmark.message).selectinload(Message.participant),
        selectinload(Bookmark.conversation)
    )
    result = await db.execute(query)
    bookmarks = result.scalars().all()
    
    if not bookmarks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No bookmarks found to export"
        )
    
    # Create export job
    from app.models.export import Export, ExportStatus, ExportFormat
    
    export = Export(
        user_id=current_user.id,
        conversation_id=None,  # Bookmarks can span multiple conversations
        format=ExportFormat(export_request.format.upper()),
        status=ExportStatus.PENDING,
        options={
            "bookmark_ids": [str(b.id) for b in bookmarks],
            "include_message_context": export_request.include_message_context,
            "type": "bookmarks"
        }
    )
    db.add(export)
    await db.commit()
    
    # Queue export job
    # TODO: Implement bookmark export task
    
    return {
        "success": True,
        "data": {
            "export_id": str(export.id),
            "status": "pending",
            "message": f"Export job created for {len(bookmarks)} bookmarks"
        }
    }


@router.get("/tags/all")
async def get_all_tags(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all unique tags used by the user
    """
    # Get all bookmarks with tags
    result = await db.execute(
        select(Bookmark.tags).where(
            Bookmark.user_id == current_user.id,
            Bookmark.deleted_at.is_(None),
            Bookmark.tags.isnot(None)
        )
    )
    
    # Extract unique tags
    all_tags = set()
    for tags, in result:
        if tags:
            all_tags.update(tags)
    
    # Count usage of each tag
    tag_counts = {}
    for tag in all_tags:
        count_result = await db.execute(
            select(func.count(Bookmark.id)).where(
                Bookmark.user_id == current_user.id,
                Bookmark.deleted_at.is_(None),
                Bookmark.tags.contains([tag])
            )
        )
        tag_counts[tag] = count_result.scalar() or 0
    
    # Sort by usage
    sorted_tags = sorted(
        [{"tag": tag, "count": count} for tag, count in tag_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    
    return {
        "success": True,
        "data": {
            "tags": sorted_tags,
            "total_tags": len(sorted_tags)
        }
    }


@router.get("/colors/all")
async def get_all_colors(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all colors used by the user with counts
    """
    result = await db.execute(
        select(
            Bookmark.color,
            func.count(Bookmark.id)
        ).where(
            Bookmark.user_id == current_user.id,
            Bookmark.deleted_at.is_(None),
            Bookmark.color.isnot(None)
        ).group_by(Bookmark.color)
    )
    
    colors = [
        {"color": color, "count": count}
        for color, count in result.all()
    ]
    
    return {
        "success": True,
        "data": {
            "colors": sorted(colors, key=lambda x: x["count"], reverse=True),
            "total_colors": len(colors)
        }
    }


# Import for selectinload and BackgroundTasks
from sqlalchemy.orm import selectinload
from fastapi import BackgroundTasks