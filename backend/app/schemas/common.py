"""
Common schemas used across the API
"""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class PaginationResponse(BaseModel):
    """Pagination metadata in responses"""
    page: int
    limit: int
    total: int
    pages: int


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: Dict[str, Any] = Field(..., description="Error details")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": {"field": "email", "error": "Invalid email format"}
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps"""
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class AuditMixin(BaseModel):
    """Mixin for models with audit fields"""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = 1


class FilterParams(BaseModel):
    """Common filter parameters"""
    search: Optional[str] = Field(None, description="Search query")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")


class BatchRequest(BaseModel):
    """Batch operation request"""
    ids: List[str] = Field(..., min_items=1, max_items=100, description="List of IDs")
    operation: str = Field(..., description="Operation to perform")
    params: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")


class BatchResponse(BaseModel):
    """Batch operation response"""
    success: bool
    processed: int
    failed: int
    results: List[Dict[str, Any]]