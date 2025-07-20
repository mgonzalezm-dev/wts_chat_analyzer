"""
Main NLP processing pipeline
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import logging
import spacy
from langdetect import detect, LangDetectException
import emoji
from app.models.conversation import Message
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ProcessedMessage:
    """Processed message with NLP results"""
    message_id: str
    language: Optional[str] = None
    tokens: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    sentiment: Optional[Dict[str, float]] = None
    keywords: List[str] = field(default_factory=list)
    emoji_count: int = 0
    word_count: int = 0
    char_count: int = 0
    has_url: bool = False
    has_email: bool = False
    has_phone: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class NLPProcessor:
    """
    Main NLP processing pipeline for messages
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize NLP processor
        
        Args:
            model_name: spaCy model name (defaults to settings)
        """
        self.model_name = model_name or settings.SPACY_MODEL
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Load spaCy model"""
        try:
            self.nlp = spacy.load(self.model_name)
            # Disable unnecessary components for speed
            disabled = ['parser', 'tagger']
            for pipe in disabled:
                if pipe in self.nlp.pipe_names:
                    self.nlp.disable_pipe(pipe)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            # Fallback to basic tokenization
            self.nlp = None
    
    async def process_message(self, message: Message) -> ProcessedMessage:
        """
        Process a single message
        
        Args:
            message: Message to process
            
        Returns:
            ProcessedMessage with NLP results
        """
        result = ProcessedMessage(message_id=str(message.id))
        
        if not message.content:
            return result
        
        # Clean content
        content = self._clean_content(message.content)
        
        # Basic statistics
        result.char_count = len(content)
        result.emoji_count = self._count_emojis(content)
        
        # Language detection
        result.language = await self._detect_language(content)
        
        # Process with spaCy if available
        if self.nlp and content:
            doc = self.nlp(content)
            
            # Tokenization
            result.tokens = [token.text for token in doc if not token.is_space]
            result.word_count = len([token for token in doc if not token.is_punct and not token.is_space])
            
            # Entity extraction
            if 'ner' in self.nlp.pipe_names:
                for ent in doc.ents:
                    result.entities.append({
                        'text': ent.text,
                        'type': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            
            # URL, email, phone detection
            result.has_url = any(token.like_url for token in doc)
            result.has_email = any(token.like_email for token in doc)
            result.has_phone = self._has_phone_number(doc)
        else:
            # Fallback processing
            words = content.split()
            result.tokens = words
            result.word_count = len(words)
            
            # Basic pattern matching
            import re
            result.has_url = bool(re.search(r'https?://\S+', content))
            result.has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
            result.has_phone = bool(re.search(r'\+?\d[\d\s\-\(\)]{8,}\d', content))
        
        return result
    
    async def process_messages_batch(
        self, 
        messages: List[Message],
        batch_size: int = None
    ) -> List[ProcessedMessage]:
        """
        Process messages in batch
        
        Args:
            messages: List of messages to process
            batch_size: Batch size for processing
            
        Returns:
            List of ProcessedMessage objects
        """
        batch_size = batch_size or settings.NLP_BATCH_SIZE
        results = []
        
        # Process in batches
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.process_message(msg) for msg in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Log progress
            if (i + batch_size) % 1000 == 0:
                logger.info(f"Processed {i + batch_size}/{len(messages)} messages")
        
        return results
    
    def _clean_content(self, content: str) -> str:
        """Clean message content"""
        if not content:
            return ""
        
        # Remove zero-width characters
        content = content.replace('\u200e', '').replace('\u200f', '')
        
        # Normalize whitespace
        content = ' '.join(content.split())
        
        return content.strip()
    
    def _count_emojis(self, text: str) -> int:
        """Count emojis in text"""
        return len([c for c in text if c in emoji.EMOJI_DATA])
    
    async def _detect_language(self, text: str) -> Optional[str]:
        """Detect language of text"""
        if not text or len(text) < 10:
            return None
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            lang = await loop.run_in_executor(None, detect, text)
            return lang
        except LangDetectException:
            return None
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    def _has_phone_number(self, doc) -> bool:
        """Check if document contains phone number"""
        # Check for phone-like patterns
        for token in doc:
            if token.like_num and len(token.text) >= 10:
                return True
        
        # Check for formatted phone numbers
        import re
        phone_pattern = r'\+?\d[\d\s\-\(\)]{8,}\d'
        return bool(re.search(phone_pattern, doc.text))
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        if not self.nlp:
            # Fallback regex
            import re
            url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
            return re.findall(url_pattern, text)
        
        doc = self.nlp(text)
        return [token.text for token in doc if token.like_url]
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        if not self.nlp:
            # Fallback regex
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            return re.findall(email_pattern, text)
        
        doc = self.nlp(text)
        return [token.text for token in doc if token.like_email]
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        import re
        
        # Various phone number patterns
        patterns = [
            r'\+\d{1,3}\s?\d{3,14}',  # International format
            r'\+\d{1,3}\s?\(\d{1,4}\)\s?\d{3,10}',  # International with area code
            r'\(\d{3}\)\s?\d{3}-?\d{4}',  # US format (xxx) xxx-xxxx
            r'\d{3}-\d{3}-\d{4}',  # US format xxx-xxx-xxxx
            r'\d{10,14}',  # Simple number string
        ]
        
        phone_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phone_numbers.extend(matches)
        
        # Remove duplicates and clean
        seen = set()
        unique_numbers = []
        for num in phone_numbers:
            cleaned = re.sub(r'[\s\-\(\)]', '', num)
            if cleaned not in seen and len(cleaned) >= 10:
                seen.add(cleaned)
                unique_numbers.append(num)
        
        return unique_numbers
    
    async def process_for_search(self, text: str) -> Dict[str, Any]:
        """
        Process text for search indexing
        
        Args:
            text: Text to process
            
        Returns:
            Dictionary with search-relevant data
        """
        # Clean text
        cleaned = self._clean_content(text)
        
        # Extract tokens for search
        if self.nlp:
            doc = self.nlp(cleaned)
            # Get lemmatized tokens, excluding stop words and punctuation
            tokens = [
                token.lemma_.lower() 
                for token in doc 
                if not token.is_stop and not token.is_punct and len(token.text) > 2
            ]
        else:
            # Fallback tokenization
            tokens = [
                word.lower() 
                for word in cleaned.split() 
                if len(word) > 2
            ]
        
        return {
            'original': text,
            'cleaned': cleaned,
            'tokens': tokens,
            'search_text': ' '.join(tokens)
        }