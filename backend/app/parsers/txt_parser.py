"""
WhatsApp text file parser implementation
"""

import re
import aiofiles
from datetime import datetime
from typing import List, Optional, Tuple, AsyncGenerator
import logging

from .base import (
    BaseParser, ParsedMessage, ParsedConversation, 
    ParsedAttachment, MessageType
)

logger = logging.getLogger(__name__)


class WhatsAppTxtParser(BaseParser):
    """
    Parser for WhatsApp .txt export files
    
    Supports various date/time formats and message patterns
    """
    
    # Common date/time patterns in WhatsApp exports
    DATE_PATTERNS = [
        # 24-hour format
        (r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\s*-\s*', '%m/%d/%Y', '%H:%M'),  # MM/DD/YYYY, HH:MM - 
        (r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\s*–\s*', '%m/%d/%Y', '%H:%M'),  # MM/DD/YYYY, HH:MM – (em dash)
        (r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}:\d{2})\s*-\s*', '%m/%d/%Y', '%H:%M:%S'),  # With seconds
        (r'(\d{1,2}-\d{1,2}-\d{2,4}),?\s+(\d{1,2}:\d{2})\s*-\s*', '%m-%d-%Y', '%H:%M'),  # MM-DD-YYYY, HH:MM - 
        (r'(\d{4}-\d{1,2}-\d{1,2}),?\s+(\d{1,2}:\d{2})\s*-\s*', '%Y-%m-%d', '%H:%M'),  # YYYY-MM-DD, HH:MM - 
        (r'(\d{1,2}\.\d{1,2}\.\d{2,4}),?\s+(\d{1,2}:\d{2})\s*-\s*', '%d.%m.%Y', '%H:%M'),  # DD.MM.YYYY, HH:MM - 
        
        # 12-hour format with AM/PM
        (r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[APap][Mm])\s*-\s*', '%m/%d/%Y', '%I:%M %p'),
        (r'(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}:\d{2}\s*[APap][Mm])\s*-\s*', '%m/%d/%Y', '%I:%M:%S %p'),
        
        # Square bracket format
        (r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2})\]\s*', '%m/%d/%Y', '%H:%M'),
        (r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}\s*[APap][Mm])\]\s*', '%m/%d/%Y', '%I:%M %p'),
    ]
    
    # Message patterns
    MESSAGE_PATTERN = r'^(.+?):\s*(.*)$'  # "Sender: Message content"
    ATTACHMENT_PATTERN = r'<attached:\s*(.+?)>'
    MEDIA_OMITTED_PATTERN = r'<Media omitted>'
    DELETED_MESSAGE_PATTERN = r'(This message was deleted|You deleted this message)'
    EDITED_MESSAGE_PATTERN = r'<This message was edited>'
    
    def __init__(self, encoding: str = 'utf-8'):
        super().__init__(encoding)
        self.current_line_number = 0
    
    async def parse_file(self, file_path: str) -> ParsedConversation:
        """Parse a WhatsApp text file"""
        async with aiofiles.open(file_path, 'r', encoding=self.encoding) as file:
            content = await file.read()
        
        return await self.parse_content(content)
    
    async def parse_content(self, content: str) -> ParsedConversation:
        """Parse WhatsApp text content"""
        lines = content.split('\n')
        conversation = ParsedConversation()
        
        current_message = None
        self.current_line_number = 0
        
        for line in lines:
            self.current_line_number += 1
            line = line.strip()
            
            if not line:
                continue
            
            # Try to parse as a new message
            parsed = self._parse_message_line(line)
            
            if parsed:
                # Save previous message if exists
                if current_message:
                    conversation.add_message(current_message)
                
                current_message = parsed
            else:
                # This is a continuation of the previous message
                if current_message:
                    if current_message.content:
                        current_message.content += '\n' + line
                    else:
                        current_message.content = line
                else:
                    # No current message, this might be a header or invalid line
                    self.add_warning(f"Orphaned line: {line}", self.current_line_number)
        
        # Don't forget the last message
        if current_message:
            conversation.add_message(current_message)
        
        # Set conversation title based on participants
        if conversation.participants:
            if len(conversation.participants) == 2:
                # Private chat
                conversation.title = f"Chat with {conversation.participants[1].display_name}"
            else:
                # Group chat
                conversation.title = f"Group chat ({len(conversation.participants)} participants)"
        
        return conversation
    
    async def parse_stream(
        self, 
        file_path: str, 
        chunk_size: int = 1000
    ) -> AsyncGenerator[List[ParsedMessage], None]:
        """Parse file in chunks for large files"""
        messages_buffer = []
        current_message = None
        
        async with aiofiles.open(file_path, 'r', encoding=self.encoding) as file:
            self.current_line_number = 0
            
            async for line in file:
                self.current_line_number += 1
                line = line.strip()
                
                if not line:
                    continue
                
                # Try to parse as a new message
                parsed = self._parse_message_line(line)
                
                if parsed:
                    # Save previous message if exists
                    if current_message:
                        messages_buffer.append(current_message)
                        
                        # Yield chunk if buffer is full
                        if len(messages_buffer) >= chunk_size:
                            yield messages_buffer
                            messages_buffer = []
                    
                    current_message = parsed
                else:
                    # This is a continuation of the previous message
                    if current_message:
                        if current_message.content:
                            current_message.content += '\n' + line
                        else:
                            current_message.content = line
            
            # Don't forget the last message
            if current_message:
                messages_buffer.append(current_message)
            
            # Yield remaining messages
            if messages_buffer:
                yield messages_buffer
    
    def _parse_message_line(self, line: str) -> Optional[ParsedMessage]:
        """Parse a single message line"""
        # Try to extract date/time
        for pattern, date_fmt, time_fmt in self.DATE_PATTERNS:
            match = re.match(pattern, line)
            if match:
                try:
                    date_str = match.group(1)
                    time_str = match.group(2)
                    
                    # Handle 2-digit years
                    if len(date_str.split('/')[-1]) == 2:
                        date_parts = date_str.split('/')
                        date_parts[-1] = '20' + date_parts[-1]
                        date_str = '/'.join(date_parts)
                    
                    # Parse datetime
                    datetime_str = f"{date_str} {time_str}"
                    datetime_fmt = f"{date_fmt} {time_fmt}"
                    timestamp = datetime.strptime(datetime_str, datetime_fmt)
                    
                    # Extract the rest of the line
                    rest_of_line = line[match.end():]
                    
                    # Parse sender and content
                    return self._parse_message_content(rest_of_line, timestamp, line)
                    
                except ValueError as e:
                    self.add_warning(f"Failed to parse date/time: {e}", self.current_line_number)
                    continue
        
        return None
    
    def _parse_message_content(
        self, 
        content: str, 
        timestamp: datetime,
        raw_line: str
    ) -> Optional[ParsedMessage]:
        """Parse message sender and content"""
        # Match sender and message
        match = re.match(self.MESSAGE_PATTERN, content)
        
        if not match:
            # System message or malformed line
            return ParsedMessage(
                timestamp=timestamp,
                sender="System",
                content=content,
                message_type=MessageType.SYSTEM,
                raw_text=raw_line
            )
        
        sender = match.group(1).strip()
        message_content = match.group(2).strip()
        
        # Create parsed message
        message = ParsedMessage(
            timestamp=timestamp,
            sender=sender,
            content=message_content,
            raw_text=raw_line
        )
        
        # Check for attachments
        attachment_match = re.search(self.ATTACHMENT_PATTERN, message_content)
        if attachment_match:
            filename = attachment_match.group(1)
            attachment = ParsedAttachment(
                filename=filename,
                attachment_type=self._detect_attachment_type(filename)
            )
            message.attachments.append(attachment)
            # Remove attachment tag from content
            message.content = re.sub(self.ATTACHMENT_PATTERN, '', message_content).strip()
        
        # Check for media omitted
        if re.search(self.MEDIA_OMITTED_PATTERN, message_content):
            message.message_type = MessageType.IMAGE  # Default to image, could be refined
            message.content = re.sub(self.MEDIA_OMITTED_PATTERN, '[Media file]', message_content).strip()
        
        # Check for deleted messages
        if re.search(self.DELETED_MESSAGE_PATTERN, message_content):
            message.is_deleted = True
            message.message_type = MessageType.DELETED
        
        # Check for edited messages
        if re.search(self.EDITED_MESSAGE_PATTERN, message_content):
            message.is_edited = True
            message.content = re.sub(self.EDITED_MESSAGE_PATTERN, '', message_content).strip()
        
        # Detect message type
        message.message_type = self.detect_message_type(
            message.content, 
            bool(message.attachments)
        )
        
        # Clean content
        if message.content:
            message.content = self.clean_text(message.content)
        
        return message
    
    def _detect_attachment_type(self, filename: str) -> str:
        """Detect attachment type from filename"""
        filename_lower = filename.lower()
        
        # Image extensions
        if any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
            return 'image'
        
        # Video extensions
        if any(filename_lower.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']):
            return 'video'
        
        # Audio extensions
        if any(filename_lower.endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a', '.opus', '.aac']):
            return 'audio'
        
        # Document extensions
        if any(filename_lower.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx']):
            return 'document'
        
        return 'other'
    
    def _extract_reply_info(self, content: str) -> Tuple[Optional[str], str]:
        """Extract reply information from message content"""
        # WhatsApp reply format varies, but often includes quoted text
        # This is a simplified implementation
        reply_pattern = r'^(?:In reply to|Replying to).*?:\s*(.+?)(?:\n|$)'
        match = re.match(reply_pattern, content, re.IGNORECASE)
        
        if match:
            reply_to = match.group(1).strip()
            # Remove reply part from content
            clean_content = content[match.end():].strip()
            return reply_to, clean_content
        
        return None, content