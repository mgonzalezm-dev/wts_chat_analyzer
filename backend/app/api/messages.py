"""
Messages API endpoints
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message, Participant
from app.core.auth import get_current_active_user
from app.schemas.message import (
    MessageResponse,
    MessageListResponse,
    MessageSearchRequest,
    MessageSearchResponse,
    MessageStats,
    MessageContext
)

router = APIRouter()


@router.get("/conversation/{conversation_id}", response_model=MessageListResponse)
async def list_messages(
    conversation_id: uuid.UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    participant_id: Optional[uuid.UUID] = None,
    message_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List messages in a conversation
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
    
    # Build query
    query = select(Message).where(
        Message.conversation_id == conversation_id,
        Message.deleted_at.is_(None)
    )
    
    # Apply filters
    if search:
        query = query.where(Message.content.ilike(f"%{search}%"))
    
    if participant_id:
        query = query.where(Message.participant_id == participant_id)
    
    if message_type:
        query = query.where(Message.message_type == message_type)
    
    if date_from:
        query = query.where(Message.timestamp >= date_from)
    
    if date_to:
        query = query.where(Message.timestamp <= date_to)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.offset((page - 1) * limit).limit(limit)
    query = query.order_by(Message.timestamp.desc())
    
    # Execute query with participant info
    query = query.options(selectinload(Message.participant))
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Format response
    return MessageListResponse(
        data={
            "messages": [
                {
                    "id": str(msg.id),
                    "conversation_id": str(msg.conversation_id),
                    "participant_id": str(msg.participant_id),
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "timestamp": msg.timestamp,
                    "sender_phone": msg.participant.phone_number,
                    "sender_name": msg.participant.display_name,
                    "is_deleted": msg.is_deleted,
                    "is_edited": msg.is_edited,
                    "reply_to_id": str(msg.reply_to_id) if msg.reply_to_id else None,
                    "media_url": msg.media_url,
                    "media_mime_type": msg.media_mime_type,
                    "media_size": msg.media_size,
                    "created_at": msg.created_at,
                    "updated_at": msg.updated_at
                }
                for msg in messages
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get single message details
    """
    # Get message with conversation info
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            Message.id == message_id,
            Conversation.owner_id == current_user.id,
            Message.deleted_at.is_(None)
        )
        .options(selectinload(Message.participant))
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        participant_id=message.participant_id,
        content=message.content,
        message_type=message.message_type,
        timestamp=message.timestamp,
        sender_phone=message.participant.phone_number,
        sender_name=message.participant.display_name,
        is_deleted=message.is_deleted,
        is_edited=message.is_edited,
        reply_to_id=message.reply_to_id,
        media_url=message.media_url,
        media_mime_type=message.media_mime_type,
        media_size=message.media_size,
        metadata=message.metadata,
        created_at=message.created_at,
        updated_at=message.updated_at
    )


@router.get("/{message_id}/context", response_model=MessageContext)
async def get_message_context(
    message_id: uuid.UUID,
    before_count: int = Query(5, ge=0, le=50),
    after_count: int = Query(5, ge=0, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get message with surrounding context
    """
    # Get the target message
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            Message.id == message_id,
            Conversation.owner_id == current_user.id,
            Message.deleted_at.is_(None)
        )
        .options(selectinload(Message.participant))
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Get messages before
    before_query = select(Message).where(
        Message.conversation_id == message.conversation_id,
        Message.timestamp < message.timestamp,
        Message.deleted_at.is_(None)
    ).order_by(Message.timestamp.desc()).limit(before_count)
    
    before_result = await db.execute(
        before_query.options(selectinload(Message.participant))
    )
    before_messages = list(reversed(before_result.scalars().all()))
    
    # Get messages after
    after_query = select(Message).where(
        Message.conversation_id == message.conversation_id,
        Message.timestamp > message.timestamp,
        Message.deleted_at.is_(None)
    ).order_by(Message.timestamp.asc()).limit(after_count)
    
    after_result = await db.execute(
        after_query.options(selectinload(Message.participant))
    )
    after_messages = after_result.scalars().all()
    
    # Count total before and after
    before_count_query = select(func.count()).select_from(Message).where(
        Message.conversation_id == message.conversation_id,
        Message.timestamp < message.timestamp,
        Message.deleted_at.is_(None)
    )
    before_total_result = await db.execute(before_count_query)
    total_before = before_total_result.scalar()
    
    after_count_query = select(func.count()).select_from(Message).where(
        Message.conversation_id == message.conversation_id,
        Message.timestamp > message.timestamp,
        Message.deleted_at.is_(None)
    )
    after_total_result = await db.execute(after_count_query)
    total_after = after_total_result.scalar()
    
    # Format response
    def format_message(msg):
        return MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            participant_id=msg.participant_id,
            content=msg.content,
            message_type=msg.message_type,
            timestamp=msg.timestamp,
            sender_phone=msg.participant.phone_number,
            sender_name=msg.participant.display_name,
            is_deleted=msg.is_deleted,
            is_edited=msg.is_edited,
            reply_to_id=msg.reply_to_id,
            media_url=msg.media_url,
            media_mime_type=msg.media_mime_type,
            media_size=msg.media_size,
            created_at=msg.created_at,
            updated_at=msg.updated_at
        )
    
    return MessageContext(
        target_message=format_message(message),
        before_messages=[format_message(msg) for msg in before_messages],
        after_messages=[format_message(msg) for msg in after_messages],
        total_before=total_before,
        total_after=total_after
    )


@router.post("/search", response_model=MessageSearchResponse)
async def search_messages(
    search_request: MessageSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search messages across conversations
    """
    import time
    start_time = time.time()
    
    # Build base query
    query = select(Message).join(Conversation).where(
        Conversation.owner_id == current_user.id,
        Message.deleted_at.is_(None)
    )
    
    # Apply search query
    query = query.where(Message.content.ilike(f"%{search_request.query}%"))
    
    # Apply filters
    if search_request.conversation_ids:
        query = query.where(Message.conversation_id.in_(search_request.conversation_ids))
    
    if search_request.participant_ids:
        query = query.where(Message.participant_id.in_(search_request.participant_ids))
    
    if search_request.message_types:
        query = query.where(Message.message_type.in_(search_request.message_types))
    
    if search_request.date_from:
        query = query.where(Message.timestamp >= search_request.date_from)
    
    if search_request.date_to:
        query = query.where(Message.timestamp <= search_request.date_to)
    
    if not search_request.include_deleted:
        query = query.where(Message.is_deleted == False)
    
    # Execute search
    query = query.options(
        selectinload(Message.participant),
        selectinload(Message.conversation)
    )
    result = await db.execute(query.limit(100))  # Limit results
    messages = result.scalars().all()
    
    # Calculate search time
    search_time_ms = int((time.time() - start_time) * 1000)
    
    # Format results with highlights
    results = []
    for msg in messages:
        # Simple highlight implementation
        highlighted_content = msg.content.replace(
            search_request.query,
            f"<mark>{search_request.query}</mark>"
        )
        
        results.append({
            "message_id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
            "timestamp": msg.timestamp,
            "sender_name": msg.participant.display_name or msg.participant.phone_number,
            "match_score": 1.0,  # Simple scoring
            "highlights": [highlighted_content[:200] + "..." if len(highlighted_content) > 200 else highlighted_content]
        })
    
    return MessageSearchResponse(
        data={
            "results": results,
            "total_results": len(results),
            "search_time_ms": search_time_ms
        }
    )


@router.get("/conversation/{conversation_id}/stats", response_model=MessageStats)
async def get_message_stats(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get message statistics for a conversation
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
    
    # Get basic counts
    total_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        )
    )
    total_messages = total_result.scalar() or 0
    
    # Count by type
    type_result = await db.execute(
        select(
            Message.message_type,
            func.count(Message.id)
        ).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).group_by(Message.message_type)
    )
    messages_by_type = dict(type_result.all())
    
    # Count text vs media
    text_messages = messages_by_type.get('text', 0)
    media_messages = sum(count for msg_type, count in messages_by_type.items() if msg_type != 'text')
    
    # Count deleted and edited
    deleted_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.is_deleted == True
        )
    )
    deleted_messages = deleted_result.scalar() or 0
    
    edited_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.is_edited == True,
            Message.deleted_at.is_(None)
        )
    )
    edited_messages = edited_result.scalar() or 0
    
    # Count messages with replies
    replies_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id,
            Message.reply_to_id.isnot(None),
            Message.deleted_at.is_(None)
        )
    )
    messages_with_replies = replies_result.scalar() or 0
    
    # Calculate average message length
    avg_length_result = await db.execute(
        select(func.avg(func.length(Message.content))).where(
            Message.conversation_id == conversation_id,
            Message.message_type == 'text',
            Message.deleted_at.is_(None)
        )
    )
    avg_message_length = float(avg_length_result.scalar() or 0)
    
    # Messages by hour
    hour_result = await db.execute(
        select(
            func.extract('hour', Message.timestamp).label('hour'),
            func.count(Message.id)
        ).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).group_by('hour')
    )
    messages_by_hour = {int(hour): count for hour, count in hour_result.all()}
    
    # Messages by day of week
    dow_result = await db.execute(
        select(
            func.extract('dow', Message.timestamp).label('dow'),
            func.count(Message.id)
        ).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).group_by('dow')
    )
    dow_map = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 
               4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    messages_by_day = {dow_map[int(dow)]: count for dow, count in dow_result.all()}
    
    # Messages by participant
    participant_result = await db.execute(
        select(
            Participant.display_name,
            Participant.phone_number,
            func.count(Message.id)
        ).join(
            Message, Message.participant_id == Participant.id
        ).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).group_by(Participant.id, Participant.display_name, Participant.phone_number)
    )
    messages_by_participant = {
        name or phone: count 
        for name, phone, count in participant_result.all()
    }
    
    return MessageStats(
        total_messages=total_messages,
        text_messages=text_messages,
        media_messages=media_messages,
        deleted_messages=deleted_messages,
        edited_messages=edited_messages,
        messages_with_replies=messages_with_replies,
        avg_message_length=round(avg_message_length, 2),
        messages_by_type=messages_by_type,
        messages_by_hour=messages_by_hour,
        messages_by_day=messages_by_day,
        messages_by_participant=messages_by_participant
    )


# Import necessary for selectinload
from sqlalchemy.orm import selectinload