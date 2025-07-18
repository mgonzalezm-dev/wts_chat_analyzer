"""
Bookmark schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from .common import TimestampMixin, PaginationResponse


class BookmarkBase(BaseModel):
    """Base bookmark schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    tags: Optional[List[str]] = Field(default_factory=list)


class BookmarkCreate(BookmarkBase):
    """Bookmark creation schema"""
    message_id: UUID = Field(..., description="ID of the message to bookmark")


class BookmarkUpdate(BaseModel):
    """Bookmark update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    tags: Optional[List[str]] = None


class BookmarkResponse(BookmarkBase, TimestampMixin):
    """Bookmark response schema"""
    id: UUID
    user_id: UUID
    conversation_id: UUID
    message_id: UUID
    
    # Message preview
    message_content: str
    message_timestamp: datetime
    sender_name: Optional[str]
    sender_phone: str
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Important Information",
                "description": "Contact details shared",
                "color": "#FF5733",
                "tags": ["contact", "important"],
                "message_id": "456e7890-e89b-12d3-a456-426614174000",
                "message_content": "My new number is +1234567890",
                "message_timestamp": "2024-01-15T10:30:00Z",
                "sender_name": "John Doe",
                "sender_phone": "+1234567890"
            }
        }


class BookmarkListResponse(BaseModel):
    """Bookmark list response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "bookmarks": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "title": "Important Information",
                            "tags": ["contact", "important"],
                            "message_content": "My new number is...",
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "limit": 20,
                        "total": 42,
                        "pages": 3
                    }
                }
            }
        }


class BookmarkFilter(BaseModel):
    """Bookmark filter parameters"""
    search: Optional[str] = Field(None, description="Search in title and description")
    conversation_id: Optional[UUID] = Field(None, description="Filter by conversation")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")


class BookmarkExportRequest(BaseModel):
    """Bookmark export request schema"""
    format: str = Field(..., regex="^(json|csv|pdf)$", description="Export format")
    bookmark_ids: Optional[List[UUID]] = Field(None, description="Specific bookmarks to export")
    include_message_context: bool = Field(True, description="Include surrounding messages")