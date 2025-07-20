"""
Message schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from .common import TimestampMixin

class MessageBase(BaseModel):
    """Base message schema"""
    content: str
    message_type: str = Field(..., regex="^(text|image|video|audio|document|location|contact|sticker)$")
    is_deleted: bool = False
    is_edited: bool = False
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(MessageBase, TimestampMixin):
    """Message response schema"""
    id: UUID
    conversation_id: UUID
    participant_id: UUID
    timestamp: datetime
    reply_to_id: Optional[UUID] = None
    media_url: Optional[str] = None
    media_mime_type: Optional[str] = None
    media_size: Optional[int] = None
    
    # Participant info
    sender_phone: str
    sender_name: Optional[str] = None
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "conversation_id": "456e7890-e89b-12d3-a456-426614174000",
                "participant_id": "789e0123-e89b-12d3-a456-426614174000",
                "content": "Hello, how are you?",
                "message_type": "text",
                "timestamp": "2024-01-15T10:30:00Z",
                "sender_phone": "+1234567890",
                "sender_name": "John Doe",
                "is_deleted": False,
                "is_edited": False
            }
        }


class MessageListResponse(BaseModel):
    """Message list response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "messages": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "content": "Hello!",
                            "message_type": "text",
                            "timestamp": "2024-01-15T10:30:00Z",
                            "sender_phone": "+1234567890",
                            "sender_name": "John Doe"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "limit": 50,
                        "total": 1500,
                        "pages": 30
                    }
                }
            }
        }


class MessageSearchRequest(BaseModel):
    """Message search request schema"""
    query: str = Field(..., min_length=1, description="Search query")
    conversation_ids: Optional[List[UUID]] = Field(None, description="Filter by conversation IDs")
    participant_ids: Optional[List[UUID]] = Field(None, description="Filter by participant IDs")
    message_types: Optional[List[str]] = Field(None, description="Filter by message types")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    include_deleted: bool = Field(False, description="Include deleted messages")
    
    @field_validator('message_types')
    def validate_message_types(cls, v):
        """Validate message types"""
        if v:
            valid_types = {'text', 'image', 'video', 'audio', 'document', 'location', 'contact', 'sticker'}
            invalid_types = set(v) - valid_types
            if invalid_types:
                raise ValueError(f"Invalid message types: {invalid_types}")
        return v


class MessageSearchResponse(BaseModel):
    """Message search response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "results": [
                        {
                            "message_id": "123e4567-e89b-12d3-a456-426614174000",
                            "conversation_id": "456e7890-e89b-12d3-a456-426614174000",
                            "content": "Hello world!",
                            "timestamp": "2024-01-15T10:30:00Z",
                            "sender_name": "John Doe",
                            "match_score": 0.95,
                            "highlights": ["Hello <mark>world</mark>!"]
                        }
                    ],
                    "total_results": 42,
                    "search_time_ms": 125
                }
            }
        }


class MessageFilter(BaseModel):
    """Message filter parameters"""
    search: Optional[str] = Field(None, description="Search in message content")
    participant_id: Optional[UUID] = Field(None, description="Filter by participant")
    message_type: Optional[str] = Field(None, regex="^(text|image|video|audio|document|location|contact|sticker)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_media: Optional[bool] = None
    is_deleted: Optional[bool] = False
    is_edited: Optional[bool] = None
    has_reply: Optional[bool] = None


class MessageStats(BaseModel):
    """Message statistics"""
    total_messages: int = 0
    text_messages: int = 0
    media_messages: int = 0
    deleted_messages: int = 0
    edited_messages: int = 0
    messages_with_replies: int = 0
    avg_message_length: float = 0.0
    messages_by_type: Dict[str, int] = Field(default_factory=dict)
    messages_by_hour: Dict[int, int] = Field(default_factory=dict)
    messages_by_day: Dict[str, int] = Field(default_factory=dict)
    messages_by_participant: Dict[str, int] = Field(default_factory=dict)


class MessageContext(BaseModel):
    """Message context for displaying surrounding messages"""
    target_message: MessageResponse
    before_messages: List[MessageResponse] = []
    after_messages: List[MessageResponse] = []
    total_before: int = 0
    total_after: int = 0