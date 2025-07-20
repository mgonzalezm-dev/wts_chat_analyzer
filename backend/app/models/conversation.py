"""
Conversation, Participant, Message, and MessageAttachment models
"""
from typing import Optional
from enum import Enum
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, 
    BigInteger, Text, Index, JSON, Integer
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship
from .base import Base


class ConversationSourceType(str, Enum):
    """Conversation source types"""
    FILE_UPLOAD = "file_upload"
    WHATSAPP_API = "whatsapp_api"


class ConversationStatus(str, Enum):
    """Conversation processing status"""
    IMPORTING = "importing"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MessageType(str, Enum):
    """Message types"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    SYSTEM = "system"


class AttachmentType(str, Enum):
    """Attachment types"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"


class Conversation(Base):
    """Conversation container model"""
    
    __tablename__ = 'conversations'
    
    # Columns
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    source_type = Column(String(50), nullable=False, default=ConversationSourceType.FILE_UPLOAD)
    title = Column(String(255), nullable=False)
    metadata = Column(JSON, default=dict)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    message_count = Column(BigInteger, default=0, nullable=False)
    status = Column(String(50), nullable=False, default=ConversationStatus.IMPORTING)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # File information (if uploaded)
    original_filename = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash
    
    # Relationships
    owner = relationship('User', back_populates='conversations')
    participants = relationship('Participant', back_populates='conversation', cascade='all, delete-orphan')
    messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan')
    analytics = relationship('ConversationAnalytics', back_populates='conversation', cascade='all, delete-orphan')
    bookmarks = relationship('Bookmark', back_populates='conversation', cascade='all, delete-orphan')
    annotations = relationship('Annotation', back_populates='conversation', cascade='all, delete-orphan')
    export_jobs = relationship('ExportJob', back_populates='conversation', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_conversations_owner', 'owner_id'),
        Index('idx_conversations_status', 'status'),
        Index('idx_conversations_imported', 'imported_at'),
        Index('idx_conversations_active', 'owner_id', postgresql_where='deleted_at IS NULL'),
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if conversation is soft deleted"""
        return self.deleted_at is not None
    
    @property
    def duration_days(self) -> Optional[int]:
        """Get conversation duration in days"""
        if self.started_at and self.ended_at:
            return (self.ended_at - self.started_at).days
        return None


class Participant(Base):
    """Conversation participant model"""
    
    __tablename__ = 'participants'
    
    # Columns
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    phone_number = Column(String(50), nullable=True)  # May be null for system messages
    display_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    is_business = Column(Boolean, default=False, nullable=False)
    metadata = Column(JSON, default=dict)
    first_message_at = Column(DateTime(timezone=True), nullable=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(BigInteger, default=0, nullable=False)
    
    # Relationships
    conversation = relationship('Conversation', back_populates='participants')
    messages = relationship('Message', back_populates='sender')
    
    # Indexes
    __table_args__ = (
        Index('idx_participants_conversation', 'conversation_id'),
        Index('idx_participants_phone', 'phone_number'),
    )


class Message(Base):
    """Message model with full-text search support"""
    
    __tablename__ = 'messages'
    
    # Columns
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('participants.id', ondelete='SET NULL'), nullable=True)
    message_id = Column(String(255), unique=True, nullable=False)  # Original WhatsApp message ID
    content = Column(Text, nullable=True)  # Can be null for media messages
    message_type = Column(String(50), nullable=False, default=MessageType.TEXT)
    metadata = Column(JSON, default=dict)  # Store additional message data
    sent_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Full-text search
    search_vector = Column(TSVECTOR, nullable=True)
    
    # Reply information
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    conversation = relationship('Conversation', back_populates='messages')
    sender = relationship('Participant', back_populates='messages')
    attachments = relationship('MessageAttachment', back_populates='message', cascade='all, delete-orphan')
    entities = relationship('MessageEntity', back_populates='message', cascade='all, delete-orphan')
    sentiment = relationship('MessageSentiment', back_populates='message', uselist=False, cascade='all, delete-orphan')
    bookmarks = relationship('Bookmark', back_populates='message')
    annotations = relationship('Annotation', back_populates='message')
    reply_to = relationship('Message', remote_side='Message.id', backref='replies')
    
    # Indexes
    __table_args__ = (
        Index('idx_messages_conversation_sent', 'conversation_id', 'sent_at'),
        Index('idx_messages_sender_sent', 'sender_id', 'sent_at'),
        Index('idx_messages_search', 'search_vector', postgresql_using='gin'),
        Index('idx_messages_type', 'message_type'),
        Index('idx_messages_reply', 'reply_to_id'),
    )
    
    @property
    def has_attachments(self) -> bool:
        """Check if message has attachments"""
        return len(self.attachments) > 0
    
    @property
    def is_media(self) -> bool:
        """Check if message is a media message"""
        return self.message_type in [
            MessageType.IMAGE, 
            MessageType.VIDEO, 
            MessageType.AUDIO, 
            MessageType.DOCUMENT,
            MessageType.STICKER
        ]


class MessageAttachment(Base):
    """Message attachment model"""
    
    __tablename__ = 'message_attachments'
    
    # Columns
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    attachment_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=True)
    storage_path = Column(String(500), nullable=True)  # S3 key or local path
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    metadata = Column(JSON, default=dict)  # Store dimensions, duration, etc.
    
    # Thumbnail for images/videos
    thumbnail_path = Column(String(500), nullable=True)
    
    # Media metadata
    width = Column(Integer, nullable=True)  # For images/videos
    height = Column(Integer, nullable=True)  # For images/videos
    duration = Column(Integer, nullable=True)  # For videos/audio in seconds
    
    # Relationships
    message = relationship('Message', back_populates='attachments')
    
    # Indexes
    __table_args__ = (
        Index('idx_attachments_message', 'message_id'),
        Index('idx_attachments_type', 'attachment_type'),
    )
    
    @property
    def is_image(self) -> bool:
        """Check if attachment is an image"""
        return self.attachment_type == AttachmentType.IMAGE
    
    @property
    def is_video(self) -> bool:
        """Check if attachment is a video"""
        return self.attachment_type == AttachmentType.VIDEO
    
    @property
    def file_extension(self) -> Optional[str]:
        """Get file extension"""
        if self.file_name:
            parts = self.file_name.split('.')
            if len(parts) > 1:
                return parts[-1].lower()
        return None