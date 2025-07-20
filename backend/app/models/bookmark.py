"""
Bookmark and Annotation models for user-generated content
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, 
    Text, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class Bookmark(Base):
    """User bookmarks for important messages"""
    
    __tablename__ = 'bookmarks'
    
    # Columns
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), nullable=True)
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color for UI
    
    # Relationships
    user = relationship('User', back_populates='bookmarks')
    conversation = relationship('Conversation', back_populates='bookmarks')
    message = relationship('Message', back_populates='bookmarks')
    
    # Indexes
    __table_args__ = (
        Index('idx_bookmarks_user', 'user_id'),
        Index('idx_bookmarks_conversation', 'conversation_id'),
        Index('idx_bookmarks_message', 'message_id'),
        Index('idx_bookmarks_user_conversation', 'user_id', 'conversation_id'),
    )


class Annotation(Base):
    """User annotations and tags for messages"""
    
    __tablename__ = 'annotations'
    
    # Columns
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)  # task, note, question, etc.
    tags = Column(JSON, default=list)  # ["urgent", "follow-up", "important"]
    
    # Priority and status for task-like annotations
    priority = Column(String(20), nullable=True)  # high, medium, low
    status = Column(String(20), nullable=True)  # open, in_progress, completed
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='annotations')
    conversation = relationship('Conversation', back_populates='annotations')
    message = relationship('Message', back_populates='annotations')
    
    # Indexes
    __table_args__ = (
        Index('idx_annotations_user', 'user_id'),
        Index('idx_annotations_conversation', 'conversation_id'),
        Index('idx_annotations_message', 'message_id'),
        Index('idx_annotations_category', 'category'),
        Index('idx_annotations_status', 'status'),
        Index('idx_annotations_tags', 'tags', postgresql_using='gin'),
    )
    
    @property
    def is_task(self) -> bool:
        """Check if annotation is a task"""
        return self.category == 'task'
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == 'completed'