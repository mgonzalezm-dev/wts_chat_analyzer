"""
Conversation schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from .common import TimestampMixin

class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(..., regex="^(file_upload|whatsapp_api)$")
    metadata: Optional[Dict[str, Any]] = None


class ConversationCreate(ConversationBase):
    """Conversation creation schema"""
    pass


class ConversationUpdate(BaseModel):
    """Conversation update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class ParticipantResponse(BaseModel):
    """Participant response schema"""
    id: UUID
    phone_number: str
    display_name: Optional[str] = None
    is_business: bool = False
    message_count: int = 0
    first_message_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True


class ConversationResponse(ConversationBase, TimestampMixin):
    """Conversation response schema"""
    id: UUID
    owner_id: UUID
    status: str
    message_count: int = 0
    participant_count: int = 0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    imported_at: datetime
    processing_time_seconds: Optional[float] = None
    file_size: Optional[int] = None
    original_filename: Optional[str] = None
    
    class Config:
        orm_mode = True


class ConversationDetailResponse(ConversationResponse):
    """Detailed conversation response schema"""
    participants: List[ParticipantResponse] = []
    analytics_available: bool = False
    bookmarks_count: int = 0
    exports_count: int = 0
    last_accessed_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Family Group Chat",
                "source_type": "file_upload",
                "status": "completed",
                "message_count": 1500,
                "participant_count": 5,
                "started_at": "2023-01-01T00:00:00Z",
                "ended_at": "2024-01-01T00:00:00Z",
                "imported_at": "2024-01-15T10:00:00Z",
                "participants": [
                    {
                        "id": "456e7890-e89b-12d3-a456-426614174000",
                        "phone_number": "+1234567890",
                        "display_name": "John Doe",
                        "message_count": 300
                    }
                ],
                "analytics_available": True
            }
        }


class ConversationListResponse(BaseModel):
    """Conversation list response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "conversations": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "title": "Family Group Chat",
                            "source_type": "file_upload",
                            "message_count": 1500,
                            "participant_count": 5,
                            "status": "completed",
                            "imported_at": "2024-01-15T10:00:00Z"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "limit": 20,
                        "total": 50,
                        "pages": 3
                    }
                }
            }
        }


class ConversationImportRequest(BaseModel):
    """Conversation import request schema"""
    source: str = Field(..., regex="^(whatsapp_api)$", description="Import source")
    api_credentials: Dict[str, str] = Field(..., description="API credentials")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range for import")
    
    @field_validator('api_credentials')
    def validate_credentials(cls, v, values):
        """Validate API credentials based on source"""
        if 'source' in values and values['source'] == 'whatsapp_api':
            required_fields = ['api_key', 'phone_number_id']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"Missing required field: {field}")
        return v


class ConversationImportResponse(BaseModel):
    """Conversation import response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "importing",
                    "message": "Import started successfully"
                }
            }
        }


class ConversationStats(BaseModel):
    """Conversation statistics schema"""
    conversation_id: UUID
    total_messages: int
    total_media: int
    total_links: int
    avg_message_length: float
    messages_per_day: float
    most_active_hour: int
    most_active_day: str
    response_time_avg_minutes: float
    
    class Config:
        orm_mode = True


class ConversationFilter(BaseModel):
    """Conversation filter parameters"""
    search: Optional[str] = Field(None, description="Search in title")
    status: Optional[str] = Field(None, regex="^(importing|processing|completed|failed)$")
    source_type: Optional[str] = Field(None, regex="^(file_upload|whatsapp_api)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_messages: Optional[int] = Field(None, ge=0)
    max_messages: Optional[int] = Field(None, ge=0)
    participant_count: Optional[int] = Field(None, ge=1)
    has_analytics: Optional[bool] = None