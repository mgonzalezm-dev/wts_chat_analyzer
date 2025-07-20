"""
Audit log model for compliance and security tracking
"""
from enum import Enum
from sqlalchemy import (
    Column, String, ForeignKey, 
    JSON, Index, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class AuditAction(str, Enum):
    """Audit log action types"""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    
    # Conversation operations
    CONVERSATION_IMPORTED = "conversation_imported"
    CONVERSATION_VIEWED = "conversation_viewed"
    CONVERSATION_EXPORTED = "conversation_exported"
    CONVERSATION_DELETED = "conversation_deleted"
    CONVERSATION_SHARED = "conversation_shared"
    
    # Data access
    MESSAGE_SEARCHED = "message_searched"
    ANALYTICS_GENERATED = "analytics_generated"
    BULK_EXPORT = "bulk_export"
    
    # Security events
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"


class ResourceType(str, Enum):
    """Resource types for audit logging"""
    USER = "user"
    CONVERSATION = "conversation"
    MESSAGE = "message"
    EXPORT = "export"
    ANALYTICS = "analytics"
    SYSTEM = "system"


class AuditLog(Base):
    """Comprehensive audit trail for GDPR compliance"""
    
    __tablename__ = 'audit_logs'
    
    # Columns
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    changes = Column(JSON, default=dict)  # Before/after values for updates
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)
    
    # Additional context
    metadata = Column(JSON, default=dict)  # Any additional context
    error_message = Column(Text, nullable=True)  # For failed actions
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_user_created', 'user_id', 'created_at'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_created', 'created_at'),
        Index('idx_audit_logs_ip', 'ip_address'),
    )
    
    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event"""
        security_actions = [
            AuditAction.LOGIN_FAILED,
            AuditAction.PERMISSION_DENIED,
            AuditAction.RATE_LIMIT_EXCEEDED,
            AuditAction.SUSPICIOUS_ACTIVITY,
            AuditAction.DATA_BREACH_ATTEMPT
        ]
        return self.action in security_actions
    
    @property
    def is_data_access(self) -> bool:
        """Check if this is a data access event"""
        data_actions = [
            AuditAction.CONVERSATION_VIEWED,
            AuditAction.CONVERSATION_EXPORTED,
            AuditAction.MESSAGE_SEARCHED,
            AuditAction.BULK_EXPORT
        ]
        return self.action in data_actions
    
    def to_gdpr_format(self) -> dict:
        """Convert to GDPR-compliant format for data requests"""
        return {
            "timestamp": self.created_at.isoformat(),
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "changes": self.changes,
            "metadata": self.metadata
        }