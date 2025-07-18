"""
Import all models to ensure they are registered with SQLAlchemy
"""

from app.models.base import Base
from app.models.user import User, Role, Permission, UserRole, RolePermission
from app.models.conversation import Conversation, Participant, Message, MessageAttachment
from app.models.analytics import MessageEntity, MessageSentiment, ConversationAnalytics, AnalyticsJob
from app.models.bookmark import Bookmark, Annotation
from app.models.export import ExportJob, ExportFile
from app.models.audit import AuditLog

# This ensures all models are imported and registered
__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "Conversation",
    "Participant",
    "Message",
    "MessageAttachment",
    "MessageEntity",
    "MessageSentiment",
    "ConversationAnalytics",
    "AnalyticsJob",
    "Bookmark",
    "Annotation",
    "ExportJob",
    "ExportFile",
    "AuditLog",
]