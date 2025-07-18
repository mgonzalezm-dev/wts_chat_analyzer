"""
Pydantic schemas for API validation
"""

from .auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    RequestPasswordResetRequest
)

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    RoleResponse,
    PermissionResponse
)

from .conversation import (
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationImportRequest,
    ConversationImportResponse,
    ParticipantResponse
)

from .message import (
    MessageBase,
    MessageResponse,
    MessageListResponse,
    MessageSearchRequest,
    MessageSearchResponse
)

from .analytics import (
    AnalyticsResponse,
    ConversationAnalyticsResponse,
    SentimentAnalysisResponse,
    KeywordAnalysisResponse,
    EntityAnalysisResponse,
    TimelineAnalysisResponse,
    ParticipantAnalyticsResponse
)

from .bookmark import (
    BookmarkBase,
    BookmarkCreate,
    BookmarkUpdate,
    BookmarkResponse,
    BookmarkListResponse
)

from .export import (
    ExportRequest,
    ExportResponse,
    ExportStatusResponse,
    ExportListResponse
)

from .search import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SearchFilters
)

from .common import (
    PaginationParams,
    PaginationResponse,
    SuccessResponse,
    ErrorResponse,
    HealthCheckResponse
)

__all__ = [
    # Auth
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "RequestPasswordResetRequest",
    
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "RoleResponse",
    "PermissionResponse",
    
    # Conversation
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationDetailResponse",
    "ConversationListResponse",
    "ConversationImportRequest",
    "ConversationImportResponse",
    "ParticipantResponse",
    
    # Message
    "MessageBase",
    "MessageResponse",
    "MessageListResponse",
    "MessageSearchRequest",
    "MessageSearchResponse",
    
    # Analytics
    "AnalyticsResponse",
    "ConversationAnalyticsResponse",
    "SentimentAnalysisResponse",
    "KeywordAnalysisResponse",
    "EntityAnalysisResponse",
    "TimelineAnalysisResponse",
    "ParticipantAnalyticsResponse",
    
    # Bookmark
    "BookmarkBase",
    "BookmarkCreate",
    "BookmarkUpdate",
    "BookmarkResponse",
    "BookmarkListResponse",
    
    # Export
    "ExportRequest",
    "ExportResponse",
    "ExportStatusResponse",
    "ExportListResponse",
    
    # Search
    "SearchRequest",
    "SearchResponse",
    "SearchResultItem",
    "SearchFilters",
    
    # Common
    "PaginationParams",
    "PaginationResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthCheckResponse"
]