"""
Base parser classes and data structures
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from enum import Enum
import hashlib


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
    DELETED = "deleted"


@dataclass
class ParsedAttachment:
    """Parsed attachment data"""
    filename: str
    attachment_type: str
    mime_type: Optional[str] = None
    size: Optional[int] = None
    caption: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedMessage:
    """Parsed message data structure"""
    timestamp: datetime
    sender: str
    content: Optional[str]
    message_type: MessageType = MessageType.TEXT
    attachments: List[ParsedAttachment] = field(default_factory=list)
    reply_to: Optional[str] = None  # Original message content or ID
    is_deleted: bool = False
    is_edited: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_text: Optional[str] = None  # Original unparsed text
    
    def generate_id(self) -> str:
        """Generate unique message ID based on content"""
        # Create a unique ID based on timestamp, sender, and content
        id_string = f"{self.timestamp.isoformat()}:{self.sender}:{self.content or 'media'}"
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]
    
    @property
    def is_media(self) -> bool:
        """Check if message contains media"""
        return self.message_type in [
            MessageType.IMAGE,
            MessageType.VIDEO,
            MessageType.AUDIO,
            MessageType.DOCUMENT,
            MessageType.STICKER
        ]


@dataclass
class ParsedParticipant:
    """Parsed participant data"""
    phone_number: Optional[str]
    display_name: str
    is_business: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.phone_number, self.display_name))
    
    def __eq__(self, other):
        if not isinstance(other, ParsedParticipant):
            return False
        return (self.phone_number, self.display_name) == (other.phone_number, other.display_name)


@dataclass
class ParsedConversation:
    """Parsed conversation data structure"""
    title: Optional[str] = None
    participants: List[ParsedParticipant] = field(default_factory=list)
    messages: List[ParsedMessage] = field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: ParsedMessage):
        """Add a message and update conversation metadata"""
        self.messages.append(message)
        
        # Update time range
        if not self.started_at or message.timestamp < self.started_at:
            self.started_at = message.timestamp
        if not self.ended_at or message.timestamp > self.ended_at:
            self.ended_at = message.timestamp
        
        # Add participant if new
        participant = ParsedParticipant(
            phone_number=self._extract_phone_number(message.sender),
            display_name=message.sender
        )
        if participant not in self.participants:
            self.participants.append(participant)
    
    def _extract_phone_number(self, sender: str) -> Optional[str]:
        """Extract phone number from sender string"""
        # Common formats:
        # "+1 234 567 8900"
        # "John Doe"
        # "+1234567890 (Business)"
        import re
        
        # Try to extract phone number
        phone_pattern = r'(\+?\d[\d\s\-\(\)]+\d)'
        match = re.search(phone_pattern, sender)
        if match:
            # Clean up the number
            number = re.sub(r'[\s\-\(\)]', '', match.group(1))
            return number
        return None
    
    @property
    def message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)
    
    @property
    def participant_count(self) -> int:
        """Get participant count"""
        return len(self.participants)


class BaseParser(ABC):
    """Abstract base class for WhatsApp parsers"""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
        self.errors_count = 0
        self.warnings = []
    
    @abstractmethod
    async def parse_file(self, file_path: str) -> ParsedConversation:
        """
        Parse a WhatsApp conversation file
        
        Args:
            file_path: Path to the file to parse
            
        Returns:
            ParsedConversation object
        """
        pass
    
    @abstractmethod
    async def parse_content(self, content: str) -> ParsedConversation:
        """
        Parse WhatsApp conversation content
        
        Args:
            content: String content to parse
            
        Returns:
            ParsedConversation object
        """
        pass
    
    async def parse_stream(
        self, 
        file_path: str, 
        chunk_size: int = 1000
    ) -> AsyncGenerator[List[ParsedMessage], None]:
        """
        Parse file in chunks for large files
        
        Args:
            file_path: Path to the file to parse
            chunk_size: Number of messages per chunk
            
        Yields:
            Lists of parsed messages
        """
        # Default implementation - subclasses can override for efficiency
        conversation = await self.parse_file(file_path)
        
        for i in range(0, len(conversation.messages), chunk_size):
            yield conversation.messages[i:i + chunk_size]
    
    def add_warning(self, message: str, line_number: Optional[int] = None):
        """Add a parsing warning"""
        warning = {
            "message": message,
            "line_number": line_number
        }
        self.warnings.append(warning)
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Remove zero-width characters
        text = text.replace('\u200e', '').replace('\u200f', '')
        # Normalize whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    @staticmethod
    def detect_message_type(content: str, has_attachment: bool = False) -> MessageType:
        """Detect message type from content"""
        if not content and not has_attachment:
            return MessageType.DELETED
        
        content_lower = content.lower() if content else ""
        
        # System messages
        system_indicators = [
            "created group",
            "added",
            "removed",
            "left",
            "changed the subject",
            "changed this group's icon",
            "turned on disappearing messages",
            "turned off disappearing messages",
            "changed the group description",
            "messages and calls are end-to-end encrypted"
        ]
        
        if any(indicator in content_lower for indicator in system_indicators):
            return MessageType.SYSTEM
        
        # Media messages (when has_attachment is True)
        if has_attachment:
            if "image" in content_lower or "photo" in content_lower:
                return MessageType.IMAGE
            elif "video" in content_lower:
                return MessageType.VIDEO
            elif "audio" in content_lower or "voice message" in content_lower:
                return MessageType.AUDIO
            elif "document" in content_lower or "pdf" in content_lower:
                return MessageType.DOCUMENT
            elif "sticker" in content_lower:
                return MessageType.STICKER
            elif "location" in content_lower:
                return MessageType.LOCATION
            elif "contact" in content_lower:
                return MessageType.CONTACT
        
        # Check for media indicators in text
        if "<media omitted>" in content_lower:
            if "image" in content_lower:
                return MessageType.IMAGE
            elif "video" in content_lower:
                return MessageType.VIDEO
            elif "audio" in content_lower:
                return MessageType.AUDIO
            elif "document" in content_lower:
                return MessageType.DOCUMENT
            elif "sticker" in content_lower:
                return MessageType.STICKER
        
        # Check for location sharing
        if "location:" in content_lower or "https://maps.google.com" in content_lower:
            return MessageType.LOCATION
        
        # Deleted messages
        if "this message was deleted" in content_lower or "you deleted this message" in content_lower:
            return MessageType.DELETED
        
        return MessageType.TEXT