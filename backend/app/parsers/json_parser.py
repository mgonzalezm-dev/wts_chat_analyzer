"""
WhatsApp JSON format parser (WhatsApp Cloud API format)
"""

import json
import aiofiles
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
import logging

from .base import (
    BaseParser, ParsedMessage, ParsedConversation, 
    ParsedAttachment, ParsedParticipant, MessageType
)

logger = logging.getLogger(__name__)


class WhatsAppJsonParser(BaseParser):
    """
    Parser for WhatsApp JSON export format (Cloud API format)
    
    Handles the JSON structure from WhatsApp Business API exports
    """
    
    def __init__(self, encoding: str = 'utf-8'):
        super().__init__(encoding)
    
    async def parse_file(self, file_path: str) -> ParsedConversation:
        """Parse a WhatsApp JSON file"""
        async with aiofiles.open(file_path, 'r', encoding=self.encoding) as file:
            content = await file.read()
        
        return await self.parse_content(content)
    
    async def parse_content(self, content: str) -> ParsedConversation:
        """Parse WhatsApp JSON content"""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        
        conversation = ParsedConversation()
        
        # Handle different JSON structures
        if isinstance(data, dict):
            # Single conversation export
            conversation = self._parse_conversation_object(data)
        elif isinstance(data, list):
            # Multiple messages
            for item in data:
                if 'messages' in item:
                    # Conversation with messages
                    conversation = self._parse_conversation_object(item)
                    break
                else:
                    # Direct message list
                    message = self._parse_message_object(item)
                    if message:
                        conversation.add_message(message)
        
        return conversation
    
    async def parse_stream(
        self, 
        file_path: str, 
        chunk_size: int = 1000
    ) -> AsyncGenerator[List[ParsedMessage], None]:
        """Parse large JSON files in chunks"""
        # For JSON, we need to load the entire file first
        # but we can yield messages in chunks
        conversation = await self.parse_file(file_path)
        
        for i in range(0, len(conversation.messages), chunk_size):
            yield conversation.messages[i:i + chunk_size]
    
    def _parse_conversation_object(self, data: Dict[str, Any]) -> ParsedConversation:
        """Parse a conversation object"""
        conversation = ParsedConversation()
        
        # Extract metadata
        if 'name' in data:
            conversation.title = data['name']
        elif 'chat_name' in data:
            conversation.title = data['chat_name']
        
        # Extract participants
        if 'participants' in data:
            for participant_data in data['participants']:
                participant = self._parse_participant(participant_data)
                if participant and participant not in conversation.participants:
                    conversation.participants.append(participant)
        
        # Extract messages
        messages_data = data.get('messages', [])
        if not messages_data and 'data' in data:
            messages_data = data['data']
        
        for msg_data in messages_data:
            message = self._parse_message_object(msg_data)
            if message:
                conversation.add_message(message)
        
        return conversation
    
    def _parse_participant(self, data: Dict[str, Any]) -> Optional[ParsedParticipant]:
        """Parse participant data"""
        if isinstance(data, str):
            # Simple string format
            return ParsedParticipant(
                phone_number=self._extract_phone_number(data),
                display_name=data
            )
        
        # Object format
        phone = data.get('phone', data.get('phone_number', data.get('id')))
        name = data.get('name', data.get('display_name', data.get('profile_name', str(phone))))
        
        if not phone and not name:
            return None
        
        return ParsedParticipant(
            phone_number=str(phone) if phone else None,
            display_name=name,
            is_business=data.get('is_business', False),
            metadata={
                'profile_picture': data.get('profile_picture'),
                'status': data.get('status')
            }
        )
    
    def _parse_message_object(self, data: Dict[str, Any]) -> Optional[ParsedMessage]:
        """Parse a message object"""
        # Extract timestamp
        timestamp = self._parse_timestamp(data)
        if not timestamp:
            self.add_warning(f"Message without timestamp: {data.get('id', 'unknown')}")
            return None
        
        # Extract sender
        sender = self._extract_sender(data)
        if not sender:
            sender = "Unknown"
        
        # Create message
        message = ParsedMessage(
            timestamp=timestamp,
            sender=sender,
            content=None,
            metadata={}
        )
        
        # Extract message ID
        if 'id' in data:
            message.metadata['original_id'] = data['id']
        
        # Extract content based on message type
        msg_type = data.get('type', 'text')
        
        if msg_type == 'text':
            message.content = data.get('text', {}).get('body', data.get('body', ''))
            message.message_type = MessageType.TEXT
        
        elif msg_type == 'image':
            message.message_type = MessageType.IMAGE
            media_data = data.get('image', {})
            message.content = media_data.get('caption', '')
            attachment = self._parse_media_attachment(media_data, 'image')
            if attachment:
                message.attachments.append(attachment)
        
        elif msg_type == 'video':
            message.message_type = MessageType.VIDEO
            media_data = data.get('video', {})
            message.content = media_data.get('caption', '')
            attachment = self._parse_media_attachment(media_data, 'video')
            if attachment:
                message.attachments.append(attachment)
        
        elif msg_type == 'audio':
            message.message_type = MessageType.AUDIO
            media_data = data.get('audio', {})
            attachment = self._parse_media_attachment(media_data, 'audio')
            if attachment:
                message.attachments.append(attachment)
        
        elif msg_type == 'document':
            message.message_type = MessageType.DOCUMENT
            media_data = data.get('document', {})
            message.content = media_data.get('caption', '')
            attachment = self._parse_media_attachment(media_data, 'document')
            if attachment:
                message.attachments.append(attachment)
        
        elif msg_type == 'location':
            message.message_type = MessageType.LOCATION
            location_data = data.get('location', {})
            lat = location_data.get('latitude')
            lon = location_data.get('longitude')
            if lat and lon:
                message.content = f"Location: {lat}, {lon}"
                if 'name' in location_data:
                    message.content += f" ({location_data['name']})"
        
        elif msg_type == 'contact':
            message.message_type = MessageType.CONTACT
            contacts = data.get('contacts', [])
            if contacts:
                contact_names = []
                for contact in contacts:
                    name = contact.get('name', {}).get('formatted_name', 'Unknown')
                    contact_names.append(name)
                message.content = f"Contact(s): {', '.join(contact_names)}"
        
        elif msg_type == 'sticker':
            message.message_type = MessageType.STICKER
            media_data = data.get('sticker', {})
            attachment = self._parse_media_attachment(media_data, 'sticker')
            if attachment:
                message.attachments.append(attachment)
        
        else:
            # Unknown type
            message.message_type = MessageType.TEXT
            message.content = f"[{msg_type}]"
            self.add_warning(f"Unknown message type: {msg_type}")
        
        # Check if message is deleted
        if data.get('deleted', False) or data.get('is_deleted', False):
            message.is_deleted = True
            message.message_type = MessageType.DELETED
        
        # Check if message is edited
        if data.get('edited', False) or data.get('is_edited', False):
            message.is_edited = True
        
        # Extract reply information
        if 'context' in data:
            context = data['context']
            if 'quoted_message_id' in context:
                message.reply_to = context['quoted_message_id']
        
        # Store additional metadata
        message.metadata.update({
            'status': data.get('status'),
            'forwarded': data.get('forwarded', False),
            'broadcast': data.get('broadcast', False),
            'starred': data.get('starred', False)
        })
        
        return message
    
    def _parse_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """Parse timestamp from various formats"""
        timestamp = None
        
        # Try different timestamp fields
        for field in ['timestamp', 'sent_at', 'created_at', 'date', 'time']:
            if field in data:
                timestamp = data[field]
                break
        
        if not timestamp:
            return None
        
        # Parse based on type
        if isinstance(timestamp, (int, float)):
            # Unix timestamp (seconds or milliseconds)
            if timestamp > 1e10:  # Milliseconds
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp)
        
        elif isinstance(timestamp, str):
            # ISO format or other string formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S%z'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp, fmt)
                except ValueError:
                    continue
        
        return None
    
    def _extract_sender(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract sender information"""
        # Try different sender fields
        sender = data.get('from')
        if not sender:
            sender = data.get('sender')
        if not sender:
            sender = data.get('author')
        if not sender:
            sender = data.get('phone')
        
        if isinstance(sender, dict):
            # Sender is an object
            return sender.get('name', sender.get('phone', sender.get('id')))
        
        return str(sender) if sender else None
    
    def _parse_media_attachment(
        self, 
        media_data: Dict[str, Any], 
        media_type: str
    ) -> Optional[ParsedAttachment]:
        """Parse media attachment data"""
        if not media_data:
            return None
        
        attachment = ParsedAttachment(
            filename=media_data.get('filename', f'{media_type}_file'),
            attachment_type=media_type,
            mime_type=media_data.get('mime_type'),
            size=media_data.get('file_size'),
            caption=media_data.get('caption'),
            metadata={
                'id': media_data.get('id'),
                'sha256': media_data.get('sha256'),
                'url': media_data.get('link', media_data.get('url'))
            }
        )
        
        return attachment
    
    def _extract_phone_number(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        import re
        
        # Remove non-numeric characters except +
        cleaned = re.sub(r'[^\d+]', '', text)
        
        # Check if it looks like a phone number
        if cleaned and (cleaned.startswith('+') or len(cleaned) >= 10):
            return cleaned
        
        return None