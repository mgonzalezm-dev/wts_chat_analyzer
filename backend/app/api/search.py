"""
Search API endpoints
"""
import time
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.db.session import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message, Participant
from app.models.bookmark import Bookmark
from app.models.audit import AuditLog, AuditAction
from app.core.auth import get_current_active_user
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchSuggestionsResponse,
    SearchSuggestion,
    AdvancedSearchRequest
)

router = APIRouter()


def highlight_text(text: str, query: str, max_length: int = 200) -> tuple[str, List[str]]:
    """
    Create snippet and highlights for search results
    """
    import re
    
    # Case-insensitive search
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = list(pattern.finditer(text))
    
    if not matches:
        return text[:max_length], []
    
    # Find best snippet around first match
    first_match = matches[0]
    start = max(0, first_match.start() - 50)
    end = min(len(text), first_match.end() + 150)
    
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    
    # Create highlights
    highlighted = pattern.sub(f"<mark>{query}</mark>", snippet)
    highlights = [highlighted]
    
    return snippet, highlights


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unified search across messages, conversations, participants, and bookmarks
    """
    start_time = time.time()
    results = []
    facets = {
        "conversations": {},
        "participants": {},
        "message_types": {}
    }
    
    # Search in messages
    if "messages" in request.search_in:
        message_query = select(Message).join(Conversation).where(
            Conversation.owner_id == current_user.id,
            Message.deleted_at.is_(None)
        )
        
        # Apply search query
        if request.fuzzy_search:
            # Use PostgreSQL full-text search if available
            message_query = message_query.where(
                or_(
                    Message.content.ilike(f"%{request.query}%"),
                    # Add fuzzy matching with pg_trgm if available
                )
            )
        else:
            message_query = message_query.where(
                Message.content.ilike(f"%{request.query}%")
            )
        
        # Apply filters
        if request.filters:
            if request.filters.conversation_ids:
                message_query = message_query.where(
                    Message.conversation_id.in_(request.filters.conversation_ids)
                )
            if request.filters.participant_ids:
                message_query = message_query.where(
                    Message.participant_id.in_(request.filters.participant_ids)
                )
            if request.filters.message_types:
                message_query = message_query.where(
                    Message.message_type.in_(request.filters.message_types)
                )
            if request.filters.date_from:
                message_query = message_query.where(
                    Message.timestamp >= request.filters.date_from
                )
            if request.filters.date_to:
                message_query = message_query.where(
                    Message.timestamp <= request.filters.date_to
                )
            if request.filters.has_media is not None:
                if request.filters.has_media:
                    message_query = message_query.where(
                        Message.message_type != 'text'
                    )
                else:
                    message_query = message_query.where(
                        Message.message_type == 'text'
                    )
        
        # Execute search with joins
        message_query = message_query.options(
            selectinload(Message.participant),
            selectinload(Message.conversation)
        )
        
        # Apply sorting
        if request.sort_by == "date":
            message_query = message_query.order_by(
                Message.timestamp.desc() if request.sort_order == "desc" else Message.timestamp.asc()
            )
        
        # Limit for performance
        message_query = message_query.limit(100)
        
        message_result = await db.execute(message_query)
        messages = message_result.scalars().all()
        
        # Process message results
        for msg in messages:
            snippet, highlights = highlight_text(msg.content, request.query)
            
            results.append(SearchResultItem(
                result_type="message",
                score=0.9,  # TODO: Implement proper scoring
                id=msg.id,
                title=f"Message from {msg.participant.display_name or msg.participant.phone_number}",
                snippet=snippet,
                highlights=highlights if request.highlight_matches else [],
                data={
                    "conversation_id": str(msg.conversation_id),
                    "conversation_title": msg.conversation.title,
                    "timestamp": msg.timestamp.isoformat(),
                    "sender_name": msg.participant.display_name,
                    "sender_phone": msg.participant.phone_number,
                    "message_type": msg.message_type
                }
            ))
            
            # Update facets
            conv_id = str(msg.conversation_id)
            facets["conversations"][conv_id] = facets["conversations"].get(conv_id, 0) + 1
            
            part_id = str(msg.participant_id)
            facets["participants"][part_id] = facets["participants"].get(part_id, 0) + 1
            
            facets["message_types"][msg.message_type] = facets["message_types"].get(msg.message_type, 0) + 1
    
    # Search in conversations
    if "conversations" in request.search_in:
        conv_query = select(Conversation).where(
            Conversation.owner_id == current_user.id,
            Conversation.deleted_at.is_(None),
            Conversation.title.ilike(f"%{request.query}%")
        )
        
        conv_result = await db.execute(conv_query.limit(20))
        conversations = conv_result.scalars().all()
        
        for conv in conversations:
            results.append(SearchResultItem(
                result_type="conversation",
                score=0.8,
                id=conv.id,
                title=conv.title,
                snippet=f"{conv.message_count} messages, {len(conv.participants)} participants",
                highlights=[],
                data={
                    "message_count": conv.message_count,
                    "participant_count": len(conv.participants),
                    "started_at": conv.started_at.isoformat() if conv.started_at else None,
                    "ended_at": conv.ended_at.isoformat() if conv.ended_at else None
                }
            ))
    
    # Search in participants
    if "participants" in request.search_in:
        part_query = select(Participant).join(Conversation).where(
            Conversation.owner_id == current_user.id,
            or_(
                Participant.display_name.ilike(f"%{request.query}%"),
                Participant.phone_number.ilike(f"%{request.query}%")
            )
        )
        
        part_result = await db.execute(part_query.limit(20))
        participants = part_result.scalars().all()
        
        for part in participants:
            results.append(SearchResultItem(
                result_type="participant",
                score=0.7,
                id=part.id,
                title=part.display_name or part.phone_number,
                snippet=f"{part.message_count} messages in conversation",
                highlights=[],
                data={
                    "phone_number": part.phone_number,
                    "message_count": part.message_count,
                    "conversation_id": str(part.conversation_id)
                }
            ))
    
    # Search in bookmarks
    if "bookmarks" in request.search_in:
        bookmark_query = select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.deleted_at.is_(None),
            or_(
                Bookmark.title.ilike(f"%{request.query}%"),
                Bookmark.description.ilike(f"%{request.query}%")
            )
        )
        
        bookmark_result = await db.execute(bookmark_query.limit(20))
        bookmarks = bookmark_result.scalars().all()
        
        for bookmark in bookmarks:
            snippet, highlights = highlight_text(
                bookmark.description or bookmark.title,
                request.query
            )
            
            results.append(SearchResultItem(
                result_type="bookmark",
                score=0.85,
                id=bookmark.id,
                title=bookmark.title,
                snippet=snippet,
                highlights=highlights if request.highlight_matches else [],
                data={
                    "conversation_id": str(bookmark.conversation_id),
                    "message_id": str(bookmark.message_id),
                    "created_at": bookmark.created_at.isoformat(),
                    "tags": bookmark.tags or []
                }
            ))
    
    # Sort results by score and apply pagination
    results.sort(key=lambda x: x.score, reverse=True)
    
    # Apply pagination
    total_results = len(results)
    start_idx = (request.page - 1) * request.limit
    end_idx = start_idx + request.limit
    paginated_results = results[start_idx:end_idx]
    
    # Calculate search time
    search_time_ms = int((time.time() - start_time) * 1000)
    
    # Log search
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.SEARCH_PERFORMED,
        resource_type="search",
        metadata={
            "query": request.query,
            "results_count": total_results,
            "search_time_ms": search_time_ms
        }
    )
    db.add(audit_log)
    await db.commit()
    
    return SearchResponse(
        data={
            "query": request.query,
            "results": [r.dict() for r in paginated_results],
            "facets": facets,
            "pagination": {
                "page": request.page,
                "limit": request.limit,
                "total": total_results,
                "pages": (total_results + request.limit - 1) // request.limit
            },
            "search_time_ms": search_time_ms
        }
    )


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    query: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search suggestions based on partial query
    """
    suggestions = []
    
    # Get recent searches (from audit log)
    recent_searches = await db.execute(
        select(AuditLog.metadata).where(
            AuditLog.user_id == current_user.id,
            AuditLog.action == AuditAction.SEARCH_PERFORMED,
            AuditLog.metadata['query'].astext.ilike(f"{query}%")
        ).order_by(AuditLog.created_at.desc()).limit(5)
    )
    
    for log in recent_searches:
        if log.metadata and 'query' in log.metadata:
            suggestions.append(SearchSuggestion(
                text=log.metadata['query'],
                type="query",
                score=0.9
            ))
    
    # Get participant name suggestions
    participant_suggestions = await db.execute(
        select(Participant.display_name).join(Conversation).where(
            Conversation.owner_id == current_user.id,
            Participant.display_name.isnot(None),
            Participant.display_name.ilike(f"{query}%")
        ).distinct().limit(5)
    )
    
    for name, in participant_suggestions:
        suggestions.append(SearchSuggestion(
            text=name,
            type="participant",
            score=0.8
        ))
    
    # Get keyword suggestions from analytics
    from app.models.analytics import ConversationAnalytics
    
    keyword_suggestions = await db.execute(
        select(ConversationAnalytics.keywords).join(Conversation).where(
            Conversation.owner_id == current_user.id
        ).limit(10)
    )
    
    keyword_matches = set()
    for keywords, in keyword_suggestions:
        if keywords:
            for kw in keywords:
                if kw.get('word', '').lower().startswith(query.lower()):
                    keyword_matches.add(kw['word'])
    
    for keyword in list(keyword_matches)[:5]:
        suggestions.append(SearchSuggestion(
            text=keyword,
            type="keyword",
            score=0.7
        ))
    
    # Sort by score and limit
    suggestions.sort(key=lambda x: x.score, reverse=True)
    suggestions = suggestions[:limit]
    
    return SearchSuggestionsResponse(
        query=query,
        suggestions=suggestions
    )


@router.post("/advanced", response_model=SearchResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Advanced search with complex queries and NLP
    """
    start_time = time.time()
    
    # Build complex query based on conditions
    base_query = select(Message).join(Conversation).where(
        Conversation.owner_id == current_user.id,
        Message.deleted_at.is_(None)
    )
    
    # Apply query conditions
    conditions = []
    for query_item in request.queries:
        field = query_item.get('field')
        value = query_item.get('value')
        operator = query_item.get('operator', 'contains')
        
        if field == 'content':
            if operator == 'contains':
                conditions.append(Message.content.ilike(f"%{value}%"))
            elif operator == 'equals':
                conditions.append(Message.content == value)
            elif operator == 'starts_with':
                conditions.append(Message.content.ilike(f"{value}%"))
            elif operator == 'ends_with':
                conditions.append(Message.content.ilike(f"%{value}"))
        elif field == 'sender':
            conditions.append(
                Participant.display_name.ilike(f"%{value}%") |
                Participant.phone_number.ilike(f"%{value}%")
            )
    
    # Apply logical operator
    if request.operator == "AND":
        base_query = base_query.where(and_(*conditions))
    else:
        base_query = base_query.where(or_(*conditions))
    
    # Apply filters
    if request.filters:
        # Same filter logic as basic search
        pass
    
    # Use NLP if enabled
    if request.use_nlp:
        # TODO: Implement NLP query understanding
        pass
    
    # Execute search
    result = await db.execute(
        base_query.options(
            selectinload(Message.participant),
            selectinload(Message.conversation)
        ).limit(200)
    )
    messages = result.scalars().all()
    
    # Group results if requested
    if request.group_by:
        # TODO: Implement grouping logic
        pass
    
    # Process results
    results = []
    for msg in messages:
        results.append(SearchResultItem(
            result_type="message",
            score=1.0,
            id=msg.id,
            title=f"Message from {msg.participant.display_name or msg.participant.phone_number}",
            snippet=msg.content[:200],
            highlights=[],
            data={
                "conversation_id": str(msg.conversation_id),
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.message_type
            }
        ))
    
    search_time_ms = int((time.time() - start_time) * 1000)
    
    return SearchResponse(
        data={
            "query": str(request.queries),
            "results": [r.dict() for r in results],
            "facets": {},
            "pagination": {
                "page": 1,
                "limit": 200,
                "total": len(results),
                "pages": 1
            },
            "search_time_ms": search_time_ms
        }
    )


# Import for selectinload
from sqlalchemy.orm import selectinload