"""
Analytics schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

class SentimentScore(BaseModel):
    """Sentiment score breakdown"""
    positive: float = Field(..., ge=0, le=1)
    negative: float = Field(..., ge=0, le=1)
    neutral: float = Field(..., ge=0, le=1)
    compound: float = Field(..., ge=-1, le=1)


class SentimentAnalysisResponse(BaseModel):
    """Sentiment analysis response schema"""
    overall_sentiment: str = Field(..., regex="^(positive|negative|neutral)$")
    sentiment_score: SentimentScore
    sentiment_by_participant: Dict[str, SentimentScore]
    sentiment_timeline: List[Dict[str, Any]]
    most_positive_messages: List[Dict[str, Any]]
    most_negative_messages: List[Dict[str, Any]]
    
    class Config:
        schema_extra = {
            "example": {
                "overall_sentiment": "positive",
                "sentiment_score": {
                    "positive": 0.65,
                    "negative": 0.15,
                    "neutral": 0.20,
                    "compound": 0.50
                },
                "sentiment_by_participant": {
                    "+1234567890": {
                        "positive": 0.70,
                        "negative": 0.10,
                        "neutral": 0.20,
                        "compound": 0.60
                    }
                }
            }
        }


class KeywordAnalysisResponse(BaseModel):
    """Keyword analysis response schema"""
    top_keywords: List[Dict[str, Any]] = Field(..., description="Top keywords with frequency")
    keyword_trends: List[Dict[str, Any]] = Field(..., description="Keyword usage over time")
    keyword_by_participant: Dict[str, List[Dict[str, Any]]] = Field(..., description="Keywords by participant")
    word_cloud_data: List[Dict[str, Any]] = Field(..., description="Data for word cloud visualization")
    
    class Config:
        schema_extra = {
            "example": {
                "top_keywords": [
                    {"keyword": "hello", "count": 150, "frequency": 0.05},
                    {"keyword": "thanks", "count": 120, "frequency": 0.04}
                ],
                "keyword_trends": [
                    {
                        "date": "2024-01-01",
                        "keywords": {"hello": 10, "thanks": 8}
                    }
                ]
            }
        }


class EntityAnalysisResponse(BaseModel):
    """Entity analysis response schema"""
    entities: Dict[str, List[Dict[str, Any]]] = Field(..., description="Extracted entities by type")
    entity_frequency: Dict[str, int] = Field(..., description="Entity frequency count")
    entity_timeline: List[Dict[str, Any]] = Field(..., description="Entity mentions over time")
    
    class Config:
        schema_extra = {
            "example": {
                "entities": {
                    "PERSON": [
                        {"text": "John", "count": 45, "confidence": 0.95}
                    ],
                    "LOCATION": [
                        {"text": "New York", "count": 12, "confidence": 0.90}
                    ],
                    "ORGANIZATION": [
                        {"text": "Google", "count": 8, "confidence": 0.88}
                    ]
                }
            }
        }


class TimelineAnalysisResponse(BaseModel):
    """Timeline analysis response schema"""
    messages_by_hour: Dict[int, int]
    messages_by_day: Dict[str, int]
    messages_by_month: Dict[str, int]
    activity_heatmap: List[Dict[str, Any]]
    peak_hours: List[int]
    peak_days: List[str]
    response_time_analysis: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "messages_by_hour": {
                    "0": 45, "1": 23, "2": 12, "3": 8
                },
                "messages_by_day": {
                    "Monday": 234, "Tuesday": 189
                },
                "peak_hours": [20, 21, 22],
                "peak_days": ["Friday", "Saturday"]
            }
        }


class ParticipantAnalyticsResponse(BaseModel):
    """Participant analytics response schema"""
    participant_id: UUID
    phone_number: str
    display_name: Optional[str]
    message_count: int
    avg_message_length: float
    response_time_avg: float
    active_hours: List[int]
    emoji_usage: Dict[str, int]
    media_shared: Dict[str, int]
    sentiment_score: SentimentScore
    top_keywords: List[Dict[str, Any]]
    
    class Config:
        orm_mode = True


class ConversationAnalyticsResponse(BaseModel):
    """Complete conversation analytics response schema"""
    conversation_id: UUID
    generated_at: datetime
    processing_time_seconds: float
    
    # Basic stats
    total_messages: int
    total_participants: int
    date_range: Dict[str, datetime]
    avg_messages_per_day: float
    
    # Analysis results
    sentiment_analysis: SentimentAnalysisResponse
    keyword_analysis: KeywordAnalysisResponse
    entity_analysis: EntityAnalysisResponse
    timeline_analysis: TimelineAnalysisResponse
    participant_analytics: List[ParticipantAnalyticsResponse]
    
    # Media stats
    media_stats: Dict[str, int]
    link_stats: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "generated_at": "2024-01-15T10:30:00Z",
                "processing_time_seconds": 2.5,
                "total_messages": 1500,
                "total_participants": 5,
                "date_range": {
                    "start": "2023-01-01T00:00:00Z",
                    "end": "2024-01-01T00:00:00Z"
                }
            }
        }


class AnalyticsResponse(BaseModel):
    """Analytics endpoint response schema"""
    success: bool = True
    data: ConversationAnalyticsResponse
    
    
class AnalyticsGenerateRequest(BaseModel):
    """Analytics generation request schema"""
    conversation_id: UUID
    force_regenerate: bool = Field(False, description="Force regeneration even if analytics exist")
    include_sections: Optional[List[str]] = Field(
        None, 
        description="Specific sections to include",
        example=["sentiment", "keywords", "timeline"]
    )
    

class AnalyticsExportRequest(BaseModel):
    """Analytics export request schema"""
    conversation_id: UUID
    format: str = Field(..., regex="^(pdf|json|csv)$", description="Export format")
    include_visualizations: bool = Field(True, description="Include charts in PDF export")
    sections: Optional[List[str]] = Field(None, description="Specific sections to export")