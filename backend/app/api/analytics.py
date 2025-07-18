"""
Analytics API endpoints
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message, Participant
from app.models.analytics import ConversationAnalytics
from app.models.audit import AuditLog, AuditAction
from app.core.auth import get_current_active_user
from app.schemas.analytics import (
    AnalyticsResponse,
    ConversationAnalyticsResponse,
    AnalyticsGenerateRequest,
    AnalyticsExportRequest,
    SentimentAnalysisResponse,
    KeywordAnalysisResponse,
    EntityAnalysisResponse,
    TimelineAnalysisResponse,
    ParticipantAnalyticsResponse,
    SentimentScore
)
from app.analytics.nlp_processor import NLPProcessor
from app.analytics.sentiment_analyzer import SentimentAnalyzer
from app.analytics.keyword_extractor import KeywordExtractor
from app.analytics.entity_extractor import EntityExtractor

router = APIRouter()


async def generate_analytics_for_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession
):
    """
    Generate analytics for a conversation (background task)
    """
    # Get all messages
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).order_by(Message.timestamp)
    )
    messages = result.scalars().all()
    
    if not messages:
        return
    
    # Initialize processors
    nlp = NLPProcessor()
    sentiment_analyzer = SentimentAnalyzer()
    keyword_extractor = KeywordExtractor()
    entity_extractor = EntityExtractor()
    
    # Process messages
    all_text = " ".join([msg.content for msg in messages if msg.message_type == 'text'])
    
    # Sentiment analysis
    sentiment_results = sentiment_analyzer.analyze_conversation(messages)
    
    # Keyword extraction
    keywords = keyword_extractor.extract_keywords(all_text)
    
    # Entity extraction
    entities = entity_extractor.extract_entities(all_text)
    
    # Create or update analytics record
    analytics = ConversationAnalytics(
        conversation_id=conversation_id,
        generated_at=datetime.utcnow(),
        sentiment_scores=sentiment_results['overall'],
        keywords=keywords[:50],  # Top 50 keywords
        entities=entities,
        timeline_data={
            'messages_by_hour': sentiment_results['timeline']['by_hour'],
            'messages_by_day': sentiment_results['timeline']['by_day']
        },
        participant_stats=sentiment_results['by_participant']
    )
    
    # Check if analytics already exist
    existing = await db.execute(
        select(ConversationAnalytics).where(
            ConversationAnalytics.conversation_id == conversation_id
        )
    )
    if existing.scalar_one_or_none():
        # Update existing
        await db.execute(
            update(ConversationAnalytics).where(
                ConversationAnalytics.conversation_id == conversation_id
            ).values(
                generated_at=analytics.generated_at,
                sentiment_scores=analytics.sentiment_scores,
                keywords=analytics.keywords,
                entities=analytics.entities,
                timeline_data=analytics.timeline_data,
                participant_stats=analytics.participant_stats
            )
        )
    else:
        db.add(analytics)
    
    await db.commit()


@router.get("/conversation/{conversation_id}", response_model=AnalyticsResponse)
async def get_conversation_analytics(
    conversation_id: uuid.UUID,
    force_regenerate: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Get analytics for a conversation
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
    
    # Check if analytics exist
    analytics_result = await db.execute(
        select(ConversationAnalytics).where(
            ConversationAnalytics.conversation_id == conversation_id
        )
    )
    analytics = analytics_result.scalar_one_or_none()
    
    # Generate if needed
    if not analytics or force_regenerate:
        # Queue generation
        background_tasks.add_task(
            generate_analytics_for_conversation,
            conversation_id,
            db
        )
        
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Analytics generation started. Please check back in a few moments."
            )
    
    # Get detailed data
    # Messages by type
    type_result = await db.execute(
        select(
            Message.message_type,
            func.count(Message.id)
        ).where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None)
        ).group_by(Message.message_type)
    )
    media_stats = dict(type_result.all())
    
    # Get participants with stats
    participants_result = await db.execute(
        select(Participant).where(
            Participant.conversation_id == conversation_id
        )
    )
    participants = participants_result.scalars().all()
    
    # Build response
    sentiment_analysis = SentimentAnalysisResponse(
        overall_sentiment="positive" if analytics.sentiment_scores.get('compound', 0) > 0 else "negative",
        sentiment_score=SentimentScore(
            positive=analytics.sentiment_scores.get('positive', 0),
            negative=analytics.sentiment_scores.get('negative', 0),
            neutral=analytics.sentiment_scores.get('neutral', 0),
            compound=analytics.sentiment_scores.get('compound', 0)
        ),
        sentiment_by_participant={
            str(p_id): SentimentScore(**scores)
            for p_id, scores in analytics.participant_stats.items()
            if 'sentiment' in scores
        },
        sentiment_timeline=analytics.timeline_data.get('sentiment_timeline', []),
        most_positive_messages=[],  # TODO: Implement
        most_negative_messages=[]   # TODO: Implement
    )
    
    keyword_analysis = KeywordAnalysisResponse(
        top_keywords=[
            {"keyword": kw['word'], "count": kw['count'], "frequency": kw['frequency']}
            for kw in analytics.keywords[:20]
        ],
        keyword_trends=analytics.timeline_data.get('keyword_trends', []),
        keyword_by_participant={},  # TODO: Implement
        word_cloud_data=analytics.keywords[:100]
    )
    
    entity_analysis = EntityAnalysisResponse(
        entities=analytics.entities,
        entity_frequency={
            entity_type: len(entities)
            for entity_type, entities in analytics.entities.items()
        },
        entity_timeline=[]  # TODO: Implement
    )
    
    timeline_analysis = TimelineAnalysisResponse(
        messages_by_hour=analytics.timeline_data.get('messages_by_hour', {}),
        messages_by_day=analytics.timeline_data.get('messages_by_day', {}),
        messages_by_month=analytics.timeline_data.get('messages_by_month', {}),
        activity_heatmap=[],  # TODO: Implement
        peak_hours=[
            hour for hour, count in sorted(
                analytics.timeline_data.get('messages_by_hour', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        ],
        peak_days=[
            day for day, count in sorted(
                analytics.timeline_data.get('messages_by_day', {}).items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        ],
        response_time_analysis={}  # TODO: Implement
    )
    
    participant_analytics = []
    for participant in participants:
        p_stats = analytics.participant_stats.get(str(participant.id), {})
        participant_analytics.append(
            ParticipantAnalyticsResponse(
                participant_id=participant.id,
                phone_number=participant.phone_number,
                display_name=participant.display_name,
                message_count=participant.message_count,
                avg_message_length=p_stats.get('avg_message_length', 0),
                response_time_avg=p_stats.get('avg_response_time', 0),
                active_hours=p_stats.get('active_hours', []),
                emoji_usage=p_stats.get('emoji_usage', {}),
                media_shared=p_stats.get('media_stats', {}),
                sentiment_score=SentimentScore(**p_stats.get('sentiment', {
                    'positive': 0, 'negative': 0, 'neutral': 1, 'compound': 0
                })),
                top_keywords=p_stats.get('keywords', [])[:10]
            )
        )
    
    response = ConversationAnalyticsResponse(
        conversation_id=conversation_id,
        generated_at=analytics.generated_at,
        processing_time_seconds=analytics.processing_time_seconds or 0,
        total_messages=conversation.message_count,
        total_participants=len(participants),
        date_range={
            "start": conversation.started_at,
            "end": conversation.ended_at
        },
        avg_messages_per_day=conversation.message_count / max(
            (conversation.ended_at - conversation.started_at).days, 1
        ) if conversation.started_at and conversation.ended_at else 0,
        sentiment_analysis=sentiment_analysis,
        keyword_analysis=keyword_analysis,
        entity_analysis=entity_analysis,
        timeline_analysis=timeline_analysis,
        participant_analytics=participant_analytics,
        media_stats=media_stats,
        link_stats={}  # TODO: Implement
    )
    
    # Log analytics view
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.ANALYTICS_VIEWED,
        resource_type="conversation",
        resource_id=conversation_id
    )
    db.add(audit_log)
    await db.commit()
    
    return AnalyticsResponse(data=response)


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_analytics(
    request: AnalyticsGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate analytics for a conversation
    """
    # Verify conversation ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == request.conversation_id,
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
    
    # Check if analytics exist and force_regenerate
    if not request.force_regenerate:
        analytics_result = await db.execute(
            select(ConversationAnalytics).where(
                ConversationAnalytics.conversation_id == request.conversation_id
            )
        )
        if analytics_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Analytics already exist. Use force_regenerate=true to regenerate."
            )
    
    # Queue generation
    background_tasks.add_task(
        generate_analytics_for_conversation,
        request.conversation_id,
        db
    )
    
    # Log analytics generation
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.ANALYTICS_GENERATED,
        resource_type="conversation",
        resource_id=request.conversation_id,
        metadata={"force_regenerate": request.force_regenerate}
    )
    db.add(audit_log)
    await db.commit()
    
    return {
        "success": True,
        "message": "Analytics generation started",
        "conversation_id": str(request.conversation_id)
    }


@router.post("/export")
async def export_analytics(
    request: AnalyticsExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Export analytics to file
    """
    # Verify conversation ownership
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == request.conversation_id,
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
    
    # Check if analytics exist
    analytics_result = await db.execute(
        select(ConversationAnalytics).where(
            ConversationAnalytics.conversation_id == request.conversation_id
        )
    )
    analytics = analytics_result.scalar_one_or_none()
    
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analytics not available. Generate analytics first."
        )
    
    # Create export job
    from app.models.export import Export, ExportStatus, ExportFormat
    
    export = Export(
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        format=ExportFormat(request.format.upper()),
        status=ExportStatus.PENDING,
        options={
            "include_visualizations": request.include_visualizations,
            "sections": request.sections,
            "type": "analytics"
        }
    )
    db.add(export)
    await db.commit()
    
    # Queue export job
    # TODO: Implement export task
    
    return {
        "success": True,
        "data": {
            "export_id": str(export.id),
            "status": "pending",
            "message": "Analytics export job created"
        }
    }


@router.get("/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of all analytics for user's conversations
    """
    # Get all conversations with analytics
    result = await db.execute(
        select(Conversation).where(
            Conversation.owner_id == current_user.id,
            Conversation.deleted_at.is_(None)
        ).join(
            ConversationAnalytics,
            ConversationAnalytics.conversation_id == Conversation.id
        )
    )
    conversations = result.scalars().all()
    
    if not conversations:
        return {
            "success": True,
            "data": {
                "total_conversations_analyzed": 0,
                "total_messages_analyzed": 0,
                "overall_sentiment": "neutral",
                "top_keywords": [],
                "most_active_conversations": []
            }
        }
    
    # Aggregate data
    total_messages = sum(conv.message_count for conv in conversations)
    
    # Get top keywords across all conversations
    all_keywords = {}
    for conv in conversations:
        if conv.analytics and conv.analytics[0].keywords:
            for kw in conv.analytics[0].keywords[:20]:
                word = kw.get('word', '')
                all_keywords[word] = all_keywords.get(word, 0) + kw.get('count', 0)
    
    top_keywords = sorted(
        [{"keyword": k, "count": v} for k, v in all_keywords.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:20]
    
    # Most active conversations
    most_active = sorted(
        conversations,
        key=lambda x: x.message_count,
        reverse=True
    )[:5]
    
    return {
        "success": True,
        "data": {
            "total_conversations_analyzed": len(conversations),
            "total_messages_analyzed": total_messages,
            "overall_sentiment": "positive",  # TODO: Calculate properly
            "top_keywords": top_keywords,
            "most_active_conversations": [
                {
                    "id": str(conv.id),
                    "title": conv.title,
                    "message_count": conv.message_count,
                    "participant_count": len(conv.participants)
                }
                for conv in most_active
            ]
        }
    }


# Import for update
from sqlalchemy import update