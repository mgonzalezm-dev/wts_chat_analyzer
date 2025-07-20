"""
Export job and file models for data export functionality
"""
from enum import Enum
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, 
    BigInteger, JSON, Index, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class ExportFormat(str, Enum):
    """Supported export formats"""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    HTML = "html"
    TXT = "txt"


class ExportStatus(str, Enum):
    """Export job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ExportJob(Base):
    """Export job tracking"""
    
    __tablename__ = 'export_jobs'
    
    # Columns
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=True)
    export_format = Column(String(20), nullable=False)
    filters = Column(JSON, default=dict)  # Date range, participants, etc.
    options = Column(JSON, default=dict)  # Include media, analytics, etc.
    status = Column(String(20), nullable=False, default=ExportStatus.PENDING)
    requested_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Progress tracking
    progress = Column(BigInteger, default=0)  # 0-100
    total_messages = Column(BigInteger, nullable=True)
    processed_messages = Column(BigInteger, default=0)
    
    # Relationships
    user = relationship('User', back_populates='export_jobs')
    conversation = relationship('Conversation', back_populates='export_jobs')
    files = relationship('ExportFile', back_populates='job', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_export_jobs_user', 'user_id'),
        Index('idx_export_jobs_status', 'status'),
        Index('idx_export_jobs_requested', 'requested_at'),
    )
    
    @property
    def is_completed(self) -> bool:
        """Check if export is completed"""
        return self.status == ExportStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if export failed"""
        return self.status == ExportStatus.FAILED
    
    @property
    def duration_seconds(self) -> int:
        """Get export duration in seconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return 0


class ExportFile(Base):
    """Generated export files"""
    
    __tablename__ = 'export_files'
    
    # Columns
    job_id = Column(UUID(as_uuid=True), ForeignKey('export_jobs.id', ondelete='CASCADE'), nullable=False)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)  # S3 key or local path
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA-256 hash
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Download tracking
    download_count = Column(BigInteger, default=0)
    last_downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    job = relationship('ExportJob', back_populates='files')
    
    # Indexes
    __table_args__ = (
        Index('idx_export_files_job', 'job_id'),
        Index('idx_export_files_expires', 'expires_at'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if file has expired"""
        if self.expires_at is None:
            return False
        from datetime import datetime
        return datetime.utcnow() > self.expires_at
    
    @property
    def file_extension(self) -> str:
        """Get file extension"""
        parts = self.file_name.split('.')
        if len(parts) > 1:
            return parts[-1].lower()
        return ''