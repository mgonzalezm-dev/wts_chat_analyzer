"""Unit tests for conversation parsers."""
import pytest
from datetime import datetime
from pathlib import Path
import json
import tempfile

from app.services.parsers.whatsapp_parser import WhatsAppParser
from app.services.parsers.base_parser import ParsedMessage, ParsedConversation


class TestWhatsAppParser:
    """Test WhatsApp parser functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create WhatsApp parser instance."""
        return WhatsAppParser()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_text_format(self, parser, sample_whatsapp_text):
        """Test parsing WhatsApp text format."""
        # Create temporary file with sample content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_whatsapp_text)
            temp_path = f.name
        
        try:
            # Parse the file
            result = parser.parse(temp_path)
            
            # Verify conversation metadata
            assert isinstance(result, ParsedConversation)
            assert len(result.participants) == 2
            assert "Alice" in result.participants
            assert "Bob" in result.participants
            assert result.message_count == 10
            
            # Verify messages
            assert len(result.messages) == 10
            
            # Check first message
            first_msg = result.messages[0]
            assert first_msg.sender == "Alice"
            assert first_msg.content == "Hey Bob! How are you?"
            assert first_msg.message_type == "text"
            
            # Check media message
            media_msg = next(m for m in result.messages if m.message_type == "media")
            assert media_msg.sender == "Bob"
            assert "Media omitted" in media_msg.content
            
            # Check emoji handling
            emoji_msg = next(m for m in result.messages if "😊" in m.content)
            assert emoji_msg.sender == "Bob"
            
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_json_format(self, parser, sample_whatsapp_json):
        """Test parsing WhatsApp JSON format."""
        # Create temporary file with JSON content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_whatsapp_json, f)
            temp_path = f.name
        
        try:
            # Parse the file
            result = parser.parse(temp_path)
            
            # Verify conversation metadata
            assert isinstance(result, ParsedConversation)
            assert len(result.participants) == 2
            assert "Alice" in result.participants
            assert "Bob" in result.participants
            assert result.message_count == 4
            
            # Verify messages
            assert len(result.messages) == 4
            
            # Check message order
            for i in range(1, len(result.messages)):
                assert result.messages[i].timestamp >= result.messages[i-1].timestamp
            
            # Check media message
            media_msg = next(m for m in result.messages if m.message_type == "media")
            assert media_msg.sender == "Bob"
            assert media_msg.content == "photo.jpg"
            
        finally:
            # Clean up
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_empty_file(self, parser):
        """Test parsing empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            assert result.message_count == 0
            assert len(result.messages) == 0
            assert len(result.participants) == 0
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_invalid_format(self, parser):
        """Test parsing file with invalid format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a valid WhatsApp export format\nJust some random text")
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            # Parser should handle gracefully and return empty conversation
            assert result.message_count == 0
            assert len(result.messages) == 0
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_multiline_messages(self, parser):
        """Test parsing messages with multiple lines."""
        multiline_chat = """[1/1/24, 10:00 AM] Alice: This is a message
that spans multiple lines
and should be parsed correctly
[1/1/24, 10:01 AM] Bob: Single line response"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(multiline_chat)
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            assert len(result.messages) == 2
            
            # Check multiline message
            first_msg = result.messages[0]
            assert "spans multiple lines" in first_msg.content
            assert "should be parsed correctly" in first_msg.content
            
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_system_messages(self, parser):
        """Test parsing system messages."""
        system_chat = """[1/1/24, 10:00 AM] Alice: Hello
[1/1/24, 10:01 AM] Bob added Charlie
[1/1/24, 10:02 AM] You deleted this message
[1/1/24, 10:03 AM] Charlie: Hi everyone!"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(system_chat)
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            
            # Should identify system messages
            system_msgs = [m for m in result.messages if m.message_type == "system"]
            assert len(system_msgs) >= 1
            
            # Should still have correct participant count
            assert "Charlie" in result.participants
            
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_date_formats(self, parser):
        """Test parsing different date formats."""
        various_dates = """[1/1/24, 10:00 AM] Alice: US format
[01/01/2024, 10:00] Bob: Full year format
[1/1/24, 22:00] Charlie: 24-hour format
[31/12/23, 11:59 PM] David: End of year"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(various_dates)
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            assert len(result.messages) == 4
            
            # All messages should have valid timestamps
            for msg in result.messages:
                assert isinstance(msg.timestamp, datetime)
                assert msg.timestamp.year in [2023, 2024]
            
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_special_characters(self, parser):
        """Test parsing messages with special characters."""
        special_chat = """[1/1/24, 10:00 AM] Alice: Check this link: https://example.com
[1/1/24, 10:01 AM] Bob: Email me at bob@example.com
[1/1/24, 10:02 AM] Charlie: Price is $100.50 or €85.75
[1/1/24, 10:03 AM] David: Code: `print("Hello, World!")`"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(special_chat)
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            assert len(result.messages) == 4
            
            # Check URL preservation
            url_msg = next(m for m in result.messages if "https://" in m.content)
            assert "https://example.com" in url_msg.content
            
            # Check email preservation
            email_msg = next(m for m in result.messages if "@" in m.content)
            assert "bob@example.com" in email_msg.content
            
            # Check currency symbols
            price_msg = next(m for m in result.messages if "$" in m.content)
            assert "$100.50" in price_msg.content
            assert "€85.75" in price_msg.content
            
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_large_conversation(self, parser):
        """Test parsing large conversation."""
        # Generate large conversation
        large_chat = []
        participants = ["Alice", "Bob", "Charlie", "David", "Eve"]
        
        for i in range(1000):
            participant = participants[i % len(participants)]
            large_chat.append(f"[1/1/24, {10 + (i // 60)}:{i % 60:02d} AM] {participant}: Message {i}")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("\n".join(large_chat))
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            assert result.message_count == 1000
            assert len(result.messages) == 1000
            assert len(result.participants) == 5
            
            # Verify message order
            for i in range(1, len(result.messages)):
                assert result.messages[i].timestamp >= result.messages[i-1].timestamp
            
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.unit
    @pytest.mark.parser
    def test_metadata_extraction(self, parser, sample_whatsapp_text):
        """Test metadata extraction from parsed conversation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_whatsapp_text)
            temp_path = f.name
        
        try:
            result = parser.parse(temp_path)
            
            # Check metadata
            assert result.metadata is not None
            assert "format" in result.metadata
            assert result.metadata["format"] == "whatsapp"
            
            # Check date range
            assert result.start_date is not None
            assert result.end_date is not None
            assert result.start_date <= result.end_date
            
            # Check message type distribution
            text_messages = [m for m in result.messages if m.message_type == "text"]
            media_messages = [m for m in result.messages if m.message_type == "media"]
            assert len(text_messages) > 0
            assert len(media_messages) > 0
            
        finally:
            Path(temp_path).unlink()