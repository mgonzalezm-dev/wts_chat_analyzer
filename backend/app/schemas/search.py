"""
Search schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID

class SearchFilters(BaseModel):
    """Search filter parameters"""
    conversation_ids: Optional[List[UUID]] = Field(None, description="Filter by conversations")
    participant_ids: Optional[List[UUID]] = Field(None, description="Filter by participants")
    message_types: Optional[List[str]] = Field(None, description="Filter by message types")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    has_media: Optional[bool] = Field(None, description="Filter messages with media")
    is_bookmarked: Optional[bool] = Field(None, description="Filter bookmarked messages")
    
    @field_validator('message_types')
    def validate_message_types(cls, v):
        """Validate message types"""
        if v:
            valid_types = {'text', 'image', 'video', 'audio', 'document', 'location', 'contact', 'sticker'}
            invalid_types = set(v) - valid_types
            if invalid_types:
                raise ValueError(f"Invalid message types: {invalid_types}")
        return v


class SearchRequest(BaseModel):
    """Search request schema"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    
    # Search scope
    search_in: List[str] = Field(
        default=["messages", "participants", "conversations"],
        description="Where to search"
    )
    
    # Filters
    filters: Optional[SearchFilters] = None
    
    # Search options
    fuzzy_search: bool = Field(True, description="Enable fuzzy matching")
    highlight_matches: bool = Field(True, description="Highlight matching text")
    include_context: bool = Field(True, description="Include surrounding messages")
    
    # Pagination
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field("relevance", regex="^(relevance|date|conversation)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")
    
    @field_validator('search_in')
    def validate_search_scope(cls, v):
        """Validate search scope"""
        valid_scopes = {'messages', 'participants', 'conversations', 'bookmarks'}
        invalid_scopes = set(v) - valid_scopes
        if invalid_scopes:
            raise ValueError(f"Invalid search scopes: {invalid_scopes}")
        return v


class SearchResultItem(BaseModel):
    """Individual search result item"""
    result_type: str = Field(..., regex="^(message|conversation|participant|bookmark)$")
    score: float = Field(..., ge=0, le=1, description="Relevance score")
    
    # Common fields
    id: UUID
    title: str
    snippet: str
    highlights: List[str] = []
    
    # Type-specific data
    data: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "result_type": "message",
                "score": 0.95,
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Message from John Doe",
                "snippet": "...meeting tomorrow at...",
                "highlights": ["meeting <mark>tomorrow</mark> at"],
                "data": {
                    "conversation_id": "456e7890-e89b-12d3-a456-426614174000",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "sender_name": "John Doe"
                }
            }
        }


class SearchResponse(BaseModel):
    """Search response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "query": "meeting tomorrow",
                    "results": [
                        {
                            "result_type": "message",
                            "score": 0.95,
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "title": "Message from John Doe",
                            "snippet": "...meeting tomorrow at...",
                            "highlights": ["meeting <mark>tomorrow</mark> at"]
                        }
                    ],
                    "facets": {
                        "conversations": {
                            "456e7890-e89b-12d3-a456-426614174000": 15
                        },
                        "participants": {
                            "789e0123-e89b-12d3-a456-426614174000": 8
                        },
                        "message_types": {
                            "text": 20,
                            "image": 3
                        }
                    },
                    "pagination": {
                        "page": 1,
                        "limit": 20,
                        "total": 42,
                        "pages": 3
                    },
                    "search_time_ms": 125
                }
            }
        }


class SearchSuggestion(BaseModel):
    """Search suggestion/autocomplete"""
    text: str
    type: str = Field(..., regex="^(query|participant|keyword)$")
    score: float = Field(..., ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions response"""
    suggestions: List[SearchSuggestion]
    query: str
    
    class Config:
        schema_extra = {
            "example": {
                "query": "meet",
                "suggestions": [
                    {"text": "meeting", "type": "query", "score": 0.95},
                    {"text": "meet tomorrow", "type": "query", "score": 0.90},
                    {"text": "meeting notes", "type": "keyword", "score": 0.85}
                ]
            }
        }


class AdvancedSearchRequest(BaseModel):
    """Advanced search request with complex queries"""
    queries: List[Dict[str, Any]] = Field(..., description="List of search conditions")
    operator: str = Field("AND", regex="^(AND|OR)$", description="Logical operator")
    filters: Optional[SearchFilters] = None
    
    # Advanced options
    use_nlp: bool = Field(True, description="Use NLP for query understanding")
    semantic_search: bool = Field(False, description="Enable semantic search")
    language: str = Field("en", description="Query language")
    
    # Results configuration
    group_by: Optional[str] = Field(None, regex="^(conversation|participant|date)$")
    include_stats: bool = Field(True, description="Include search statistics")
    
    class Config:
        schema_extra = {
            "example": {
                "queries": [
                    {"field": "content", "value": "meeting", "operator": "contains"},
                    {"field": "sender", "value": "John", "operator": "equals"}
                ],
                "operator": "AND",
                "use_nlp": True
            }
        }