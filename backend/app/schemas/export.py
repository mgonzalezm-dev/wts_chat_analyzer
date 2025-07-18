"""
Export schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID

from .common import TimestampMixin


class ExportRequest(BaseModel):
    """Export request schema"""
    conversation_id: UUID = Field(..., description="Conversation to export")
    format: str = Field(..., regex="^(pdf|csv|json|txt|html)$", description="Export format")
    
    # Export options
    include_media: bool = Field(False, description="Include media files in export")
    include_analytics: bool = Field(False, description="Include analytics in export")
    include_metadata: bool = Field(True, description="Include message metadata")
    
    # Filters
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    participant_ids: Optional[List[UUID]] = Field(None, description="Filter by participants")
    message_types: Optional[List[str]] = Field(None, description="Filter by message types")
    
    # PDF specific options
    pdf_options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "page_size": "A4",
            "orientation": "portrait",
            "include_toc": True,
            "include_cover": True,
            "font_size": 10
        }
    )
    
    @validator('message_types')
    def validate_message_types(cls, v):
        """Validate message types"""
        if v:
            valid_types = {'text', 'image', 'video', 'audio', 'document', 'location', 'contact', 'sticker'}
            invalid_types = set(v) - valid_types
            if invalid_types:
                raise ValueError(f"Invalid message types: {invalid_types}")
        return v


class ExportResponse(BaseModel):
    """Export response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "export_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "processing",
                    "format": "pdf",
                    "message": "Export job created successfully"
                }
            }
        }


class ExportStatusResponse(BaseModel):
    """Export status response schema"""
    id: UUID
    conversation_id: UUID
    format: str
    status: str = Field(..., regex="^(pending|processing|completed|failed|cancelled)$")
    progress: int = Field(..., ge=0, le=100)
    
    # File info (when completed)
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    expires_at: Optional[datetime] = None
    
    # Export details
    total_messages: Optional[int] = None
    exported_messages: Optional[int] = None
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error info (if failed)
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "conversation_id": "456e7890-e89b-12d3-a456-426614174000",
                "format": "pdf",
                "status": "completed",
                "progress": 100,
                "file_url": "/api/v1/exports/123e4567-e89b-12d3-a456-426614174000/download",
                "file_size": 2048576,
                "expires_at": "2024-01-16T10:30:00Z",
                "total_messages": 1500,
                "exported_messages": 1500,
                "created_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:05:00Z"
            }
        }


class ExportListResponse(BaseModel):
    """Export list response schema"""
    success: bool = True
    data: dict
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "exports": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "conversation_id": "456e7890-e89b-12d3-a456-426614174000",
                            "format": "pdf",
                            "status": "completed",
                            "created_at": "2024-01-15T10:00:00Z",
                            "file_size": 2048576
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "limit": 20,
                        "total": 15,
                        "pages": 1
                    }
                }
            }
        }


class ExportFilter(BaseModel):
    """Export filter parameters"""
    conversation_id: Optional[UUID] = Field(None, description="Filter by conversation")
    format: Optional[str] = Field(None, regex="^(pdf|csv|json|txt|html)$")
    status: Optional[str] = Field(None, regex="^(pending|processing|completed|failed|cancelled)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class BulkExportRequest(BaseModel):
    """Bulk export request schema"""
    conversation_ids: List[UUID] = Field(..., min_items=1, max_items=10)
    format: str = Field(..., regex="^(pdf|csv|json|txt|html)$")
    merge_files: bool = Field(False, description="Merge all exports into single file")
    export_options: Optional[ExportRequest] = None