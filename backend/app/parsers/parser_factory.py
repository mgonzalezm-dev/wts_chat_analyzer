"""
Parser factory for automatic format detection and parser selection
"""

import os
import magic
import chardet
from typing import Optional, Type, BinaryIO
import logging

from .base import BaseParser
from .txt_parser import WhatsAppTxtParser
from .json_parser import WhatsAppJsonParser

logger = logging.getLogger(__name__)


class FileFormat:
    """Supported file formats"""
    TEXT = "text"
    JSON = "json"
    UNKNOWN = "unknown"


def detect_file_format(file_path: str) -> str:
    """
    Detect file format using multiple methods
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected format (FileFormat constant)
    """
    # First, check file extension
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.txt':
        return FileFormat.TEXT
    elif ext == '.json':
        return FileFormat.JSON
    
    # If extension is not conclusive, check MIME type
    try:
        mime = magic.from_file(file_path, mime=True)
        
        if mime.startswith('text/'):
            # Check if it's actually JSON
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
                if sample.strip().startswith(b'{') or sample.strip().startswith(b'['):
                    return FileFormat.JSON
            return FileFormat.TEXT
        elif mime == 'application/json':
            return FileFormat.JSON
    except Exception as e:
        logger.warning(f"Failed to detect MIME type: {e}")
    
    # Last resort: check content
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(4096)
            
            # Detect encoding
            detected = chardet.detect(sample)
            encoding = detected['encoding'] or 'utf-8'
            
            # Try to decode and check content
            text = sample.decode(encoding, errors='ignore')
            
            # Check for JSON markers
            if text.strip().startswith('{') or text.strip().startswith('['):
                try:
                    import json
                    json.loads(text)
                    return FileFormat.JSON
                except:
                    pass
            
            # Check for WhatsApp text format markers
            import re
            # Look for date/time patterns common in WhatsApp exports
            if re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}.*\d{1,2}:\d{2}', text):
                return FileFormat.TEXT
    
    except Exception as e:
        logger.error(f"Failed to detect file format: {e}")
    
    return FileFormat.UNKNOWN


def detect_encoding(file_path: str) -> str:
    """
    Detect file encoding
    
    Args:
        file_path: Path to the file
        
    Returns:
        Detected encoding (defaults to utf-8)
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            if encoding and confidence > 0.7:
                logger.info(f"Detected encoding: {encoding} (confidence: {confidence})")
                return encoding
    except Exception as e:
        logger.warning(f"Failed to detect encoding: {e}")
    
    return 'utf-8'


class ParserFactory:
    """Factory for creating appropriate parser instances"""
    
    # Registry of parsers
    _parsers = {
        FileFormat.TEXT: WhatsAppTxtParser,
        FileFormat.JSON: WhatsAppJsonParser,
    }
    
    @classmethod
    def create_parser(
        cls, 
        file_path: Optional[str] = None,
        file_format: Optional[str] = None,
        encoding: Optional[str] = None
    ) -> BaseParser:
        """
        Create appropriate parser instance
        
        Args:
            file_path: Path to file (for auto-detection)
            file_format: Explicit format specification
            encoding: File encoding (auto-detected if not provided)
            
        Returns:
            Parser instance
            
        Raises:
            ValueError: If format cannot be determined or is unsupported
        """
        # Determine format
        if file_format:
            format_type = file_format
        elif file_path:
            format_type = detect_file_format(file_path)
        else:
            raise ValueError("Either file_path or file_format must be provided")
        
        # Get parser class
        parser_class = cls._parsers.get(format_type)
        if not parser_class:
            raise ValueError(f"Unsupported file format: {format_type}")
        
        # Determine encoding
        if not encoding and file_path:
            encoding = detect_encoding(file_path)
        elif not encoding:
            encoding = 'utf-8'
        
        # Create parser instance
        return parser_class(encoding=encoding)
    
    @classmethod
    def register_parser(cls, format_type: str, parser_class: Type[BaseParser]):
        """
        Register a new parser type
        
        Args:
            format_type: Format identifier
            parser_class: Parser class
        """
        cls._parsers[format_type] = parser_class
    
    @classmethod
    def get_supported_formats(cls) -> list:
        """Get list of supported formats"""
        return list(cls._parsers.keys())


async def parse_whatsapp_file(
    file_path: str,
    file_format: Optional[str] = None,
    encoding: Optional[str] = None
):
    """
    Convenience function to parse a WhatsApp file
    
    Args:
        file_path: Path to the file
        file_format: Optional format override
        encoding: Optional encoding override
        
    Returns:
        ParsedConversation object
    """
    parser = ParserFactory.create_parser(
        file_path=file_path,
        file_format=file_format,
        encoding=encoding
    )
    
    return await parser.parse_file(file_path)


async def parse_whatsapp_content(
    content: str,
    file_format: str,
    encoding: str = 'utf-8'
):
    """
    Convenience function to parse WhatsApp content
    
    Args:
        content: String content to parse
        file_format: Format of the content
        encoding: Content encoding
        
    Returns:
        ParsedConversation object
    """
    parser = ParserFactory.create_parser(
        file_format=file_format,
        encoding=encoding
    )
    
    return await parser.parse_content(content)