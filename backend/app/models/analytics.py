"""
Analytics models for message analysis and conversation insights
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, 
    Integer, JSON, Date, Index, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class EntityType(str, Enum):
    """Named entity types"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    MONEY = "money"
    PHONE = "phone"
    EMAIL = "email"
    URL = "url"
    HASHTAG = "hashtag"
    MENTION = "mention"


class SentimentLabel(str, Enum):
    """Sentiment classification labels"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class AnalyticsJobType(str, Enum):
    """Analytics job types"""
    FULL_ANALYSIS = "full_analysis"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ENTITY_EXTRACTION = "entity_extraction"
    KEYWORD_EXTRACTION = "keyword_extraction"
    SUMMARY_GENERATION = "summary_generation"


class AnalyticsJobStatus(str, Enum):
    """Analytics job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageEntity(Base):
    """Extracted entities from messages"""
    
    __tablename__ = 'message_entities'
    
    # Columns
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_value = Column(String(500), nullable=False)
    start_position = Column(Integer, nullable=True)  # Character position in message
    end_position = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    metadata = Column(JSON, default=dict)  # Additional entity information
    
    # Relationships
    message = relationship('Message', back_populates='entities')
    
    # Indexes
    __table_args__ = (
        Index('idx_entities_message', 'message_id'),
        Index('idx_entities_type', 'entity_type'),
        Index('idx_entities_value', 'entity_value'),
    )


class MessageSentiment(Base):
    """Sentiment analysis results for messages"""
    
    __tablename__ = 'message_sentiments'
    
    # Use message_id as primary key (one-to-one relationship)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete='CASCADE'), primary_key=True)
    
    # Sentiment scores
    polarity = Column(Float, nullable=False)  # -1.0 (negative) to 1.0 (positive)
    subjectivity = Column(Float, nullable=False)  # 0.0 (objective) to 1.0 (subjective)
    sentiment_label = Column(String(50), nullable=False)
    
    # Emotion scores (optional, from advanced models)
    emotion_scores = Column(JSON, default=dict)  # {"joy": 0.8, "anger": 0.1, ...}
    
    # Analysis metadata
    analyzed_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    model_version = Column(String(50), nullable=True)
    
    # Relationships
    message = relationship('Message', back_populates='sentiment', uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_sentiment_label', 'sentiment_label'),
        Index('idx_sentiment_polarity', 'polarity'),
    )
    
    @property
    def is_positive(self) -> bool:
        """Check if sentiment is positive"""
        return self.polarity > 0.1
    
    @property
    def is_negative(self) -> bool:
        """Check if sentiment is negative"""
        return self.polarity < -0.1
    
    @property
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral"""
        return -0.1 <= self.polarity <= 0.1


class ConversationAnalytics(Base):
    """Pre-computed analytics for conversations"""
    
    __tablename__ = 'conversation_analytics'
    
    # Columns
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey('analytics_jobs.id', ondelete='SET NULL'), nullable=True)
    analysis_date = Column(Date, nullable=False)
    
    # Daily statistics
    daily_stats = Column(JSON, nullable=False, default=dict)
    """
    {
        "message_count": 150,
        "active_participants": 5,
        "peak_hour": 14,
        "avg_message_length": 45.2,
        "media_count": 12,
        "links_shared": 3
    }
    """
    
    # Participant statistics
    participant_stats = Column(JSON, nullable=False, default=dict)
    """
    {
        "participant_id": {
            "message_count": 50,
            "avg_response_time": 300,  # seconds
            "initiated_conversations": 5,
            "sentiment_avg": 0.3
        }
    }
    """
    
    # Keyword frequencies
    keyword_frequencies = Column(JSON, nullable=False, default=dict)
    """
    {
        "keywords": [
            {"word": "meeting", "count": 15, "tfidf": 0.85},
            {"word": "project", "count": 12, "tfidf": 0.72}
        ],
        "bigrams": [
            {"phrase": "team meeting", "count": 8, "tfidf": 0.91}
        ],
        "topics": [
            {"topic": "work", "score": 0.75, "keywords": ["meeting", "project", "deadline"]}
        ]
    }
    """
    
    # Response time analysis
    response_times = Column(JSON, nullable=False, default=dict)
    """
    {
        "avg_response_time": 450,  # seconds
        "median_response_time": 300,
        "response_time_by_hour": {
            "0": 1200, "1": 1500, ..., "23": 600
        },
        "response_patterns": {
            "immediate": 0.3,  # < 1 min
            "quick": 0.4,      # 1-5 min
            "delayed": 0.3     # > 5 min
        }
    }
    """
    
    # Sentiment trends
    sentiment_trends = Column(JSON, nullable=False, default=dict)
    """
    {
        "overall_sentiment": 0.25,
        "sentiment_by_participant": {
            "participant_id": 0.4
        },
        "sentiment_over_time": [
            {"date": "2024-01-01", "sentiment": 0.3},
            {"date": "2024-01-02", "sentiment": 0.2}
        ],
        "emotion_distribution": {
            "joy": 0.4,
            "neutral": 0.5,
            "anger": 0.1
        }
    }
    """
    
    # Activity patterns
    activity_patterns = Column(JSON, nullable=False, default=dict)
    """
    {
        "most_active_day": "Monday",
        "most_active_hour": 14,
        "weekend_activity_ratio": 0.2,
        "night_activity_ratio": 0.1,
        "conversation_initiators": {
            "participant_id": 0.4  # percentage of conversations initiated
        }
    }
    """
    
    # Relationships
    conversation = relationship('Conversation', back_populates='analytics')
    job = relationship('AnalyticsJob')
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_conversation_date', 'conversation_id', 'analysis_date'),
        Index('idx_analytics_date', 'analysis_date'),
    )


class AnalyticsJob(Base):
    """Background analytics job tracking"""
    
    __tablename__ = 'analytics_jobs'
    
    # Columns
    job_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=AnalyticsJobStatus.PENDING)
    parameters = Column(JSON, default=dict)  # Job configuration
    scheduled_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Progress tracking
    progress = Column(Integer, default=0)  # 0-100
    total_items = Column(Integer, nullable=True)
    processed_items = Column(Integer, default=0)
    
    # Results summary
    results_summary = Column(JSON, default=dict)
    
    # Relationships
    analytics_results = relationship('ConversationAnalytics', back_populates='job')
    
    # Indexes
    __table_args__ = (
        Index('idx_jobs_status', 'status'),
        Index('idx_jobs_type', 'job_type'),
        Index('idx_jobs_scheduled', 'scheduled_at'),
    )
    
    @property
    def duration_seconds(self) -> int:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return 0
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running"""
        return self.status == AnalyticsJobStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed"""
        return self.status == AnalyticsJobStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed"""
        return self.status == AnalyticsJobStatus.FAILED