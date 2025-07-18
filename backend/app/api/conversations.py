"""
Conversations API endpoints
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation, ConversationStatus, ConversationSourceType
from app.models.audit import AuditLog, AuditAction
from app.core.auth import get_current_active_user, require_permission
from app.parsers import ParserFactory
from app.config import settings
from app.utils.file_storage import FileStorage
from app.tasks.ingestion import process_conversation_file

router = APIRouter()


# Request/Response models
class ConversationResponse(BaseModel):
    id: str
    title: str
    source_type: str
    message_count: int
    participant_count: int
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    imported_at: datetime
    status: str
    metadata: dict = {}


class ConversationListResponse(BaseModel):
    success: bool = True
    data: dict


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    source_type: str
    message_count: int
    participant_count: int
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    imported_at: datetime
    status: str
    metadata: dict = {}
    participants: List[dict] = []
    analytics_available: bool = False


class ImportRequest(BaseModel):
    source: str = Field(..., description="Source type: 'whatsapp_api'")
    api_credentials: dict = Field(..., description="API credentials")
    date_range: Optional[dict] = None


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List conversations for authenticated user
    """
    # Build query
    query = select(Conversation).where(
        Conversation.owner_id == current_user.id,
        Conversation.deleted_at.is_(None)
    )
    
    # Apply filters
    if search:
        query = query.where(
            Conversation.title.ilike(f"%{search}%")
        )
    
    if date_from:
        query = query.where(Conversation.imported_at >= date_from)
    
    if date_to:
        query = query.where(Conversation.imported_at <= date_to)
    
    if status:
        query = query.where(Conversation.status == status)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.offset((page - 1) * limit).limit(limit)
    query = query.order_by(Conversation.imported_at.desc())
    
    # Execute query
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    # Format response
    return ConversationListResponse(
        data={
            "conversations": [
                {
                    "id": str(conv.id),
                    "title": conv.title,
                    "source_type": conv.source_type,
                    "message_count": conv.message_count,
                    "participant_count": len(conv.participants),
                    "started_at": conv.started_at,
                    "ended_at": conv.ended_at,
                    "imported_at": conv.imported_at,
                    "status": conv.status
                }
                for conv in conversations
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )


@router.post("/import")
async def import_conversation(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    import_request: Optional[ImportRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Import new conversation from file or API
    """
    if file and import_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either file upload or API import, not both"
        )
    
    if not file and not import_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either file upload or API import configuration"
        )
    
    # File upload
    if file:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file"
            )
        
        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {settings.ALLOWED_UPLOAD_EXTENSIONS}"
            )
        
        # Check file size
        if file.size and file.size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )
        
        # Save file
        file_storage = FileStorage()
        file_path = await file_storage.save_upload(file, current_user.id)
        
        # Create conversation record
        conversation = Conversation(
            owner_id=current_user.id,
            source_type=ConversationSourceType.FILE_UPLOAD,
            title=f"Import from {file.filename}",
            status=ConversationStatus.IMPORTING,
            original_filename=file.filename,
            file_size=file.size,
            metadata={"file_path": file_path}
        )
        db.add(conversation)
        await db.commit()
        
        # Log import
        audit_log = AuditLog(
            user_id=current_user.id,
            action=AuditAction.CONVERSATION_IMPORTED,
            resource_type="conversation",
            resource_id=conversation.id,
            metadata={"filename": file.filename, "size": file.size}
        )
        db.add(audit_log)
        await db.commit()
        
        # Queue processing job
        background_tasks.add_task(
            process_conversation_file,
            conversation_id=str(conversation.id),
            file_path=file_path
        )
        
        return {
            "success": True,
            "data": {
                "conversation_id": str(conversation.id),
                "status": "importing",
                "message": "File uploaded successfully. Processing will begin shortly."
            }
        }
    
    # API import
    else:
        # TODO: Implement WhatsApp API import
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WhatsApp API import not implemented yet"
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation details with metadata
    """
    # Get conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == current_user.id,
            Conversation.deleted_at.is_(None)
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Log view
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CONVERSATION_VIEWED,
        resource_type="conversation",
        resource_id=conversation.id
    )
    db.add(audit_log)
    await db.commit()
    
    # Check if analytics are available
    analytics_available = len(conversation.analytics) > 0
    
    return ConversationDetailResponse(
        id=str(conversation.id),
        title=conversation.title,
        source_type=conversation.source_type,
        message_count=conversation.message_count,
        participant_count=len(conversation.participants),
        started_at=conversation.started_at,
        ended_at=conversation.ended_at,
        imported_at=conversation.imported_at,
        status=conversation.status,
        metadata=conversation.metadata or {},
        participants=[
            {
                "id": str(p.id),
                "phone_number": p.phone_number,
                "display_name": p.display_name,
                "message_count": p.message_count,
                "first_message_at": p.first_message_at,
                "last_message_at": p.last_message_at
            }
            for p in conversation.participants
        ],
        analytics_available=analytics_available
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete conversation (soft delete)
    """
    # Get conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == current_user.id,
            Conversation.deleted_at.is_(None)
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Soft delete
    conversation.deleted_at = datetime.utcnow()
    
    # Log deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CONVERSATION_DELETED,
        resource_type="conversation",
        resource_id=conversation.id
    )
    db.add(audit_log)
    await db.commit()
    
    return {"success": True, "message": "Conversation deleted successfully"}


@router.get("/{conversation_id}/participants")
async def get_conversation_participants(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation participants
    """
    # Verify conversation ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.owner_id == current_user.id,
            Conversation.deleted_at.is_(None)
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return {
        "success": True,
        "data": {
            "participants": [
                {
                    "id": str(p.id),
                    "phone_number": p.phone_number,
                    "display_name": p.display_name,
                    "is_business": p.is_business,
                    "message_count": p.message_count,
                    "first_message_at": p.first_message_at,
                    "last_message_at": p.last_message_at,
                    "metadata": p.metadata or {}
                }
                for p in conversation.participants
            ]
        }
    }