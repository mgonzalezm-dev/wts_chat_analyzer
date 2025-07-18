"""
Entity extraction module for identifying named entities, URLs, emails, etc.
"""

import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
import spacy
from spacy.tokens import Doc

from app.models.conversation import Message
from app.models.analytics import EntityType

logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extract entities from messages including:
    - Named entities (people, organizations, locations)
    - Phone numbers
    - Email addresses
    - URLs
    - Hashtags
    - Mentions
    """
    
    def __init__(self, nlp_model=None):
        """
        Initialize entity extractor
        
        Args:
            nlp_model: Pre-loaded spaCy model (optional)
        """
        self.nlp = nlp_model
        if not self.nlp:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded spaCy model for entity extraction")
            except Exception as e:
                logger.error(f"Failed to load spaCy model: {e}")
                self.nlp = None
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for entity extraction"""
        self.patterns = {
            'phone': re.compile(
                r'(?:(?:\+|00)\d{1,3}[\s-]?)?\(?\d{1,4}\)?[\s-]?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{0,4}'
            ),
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            'url': re.compile(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            ),
            'hashtag': re.compile(r'#\w+'),
            'mention': re.compile(r'@\w+'),
            'date': re.compile(
                r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'
            ),
            'time': re.compile(
                r'\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?:\s*[AaPp][Mm])?\b'
            ),
            'money': re.compile(
                r'(?:[$€£¥₹]\s*\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|euros?|pounds?|USD|EUR|GBP))'
            )
        }
    
    async def extract_entities(self, message: Message) -> List[Dict[str, Any]]:
        """
        Extract all entities from a message
        
        Args:
            message: Message to process
            
        Returns:
            List of extracted entities
        """
        if not message.content:
            return []
        
        entities = []
        
        # Extract using spaCy if available
        if self.nlp:
            entities.extend(await self._extract_spacy_entities(message.content))
        
        # Extract using regex patterns
        entities.extend(self._extract_pattern_entities(message.content))
        
        # Remove duplicates
        entities = self._deduplicate_entities(entities)
        
        return entities
    
    async def extract_entities_batch(
        self, 
        messages: List[Message]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract entities from multiple messages
        
        Args:
            messages: List of messages
            
        Returns:
            Dictionary mapping message IDs to entity lists
        """
        tasks = [self.extract_entities(msg) for msg in messages]
        results = await asyncio.gather(*tasks)
        
        return {
            str(msg.id): entities 
            for msg, entities in zip(messages, results)
        }
    
    async def _extract_spacy_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy"""
        if not self.nlp:
            return []
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, self.nlp, text)
        
        entities = []
        
        # Extract named entities
        for ent in doc.ents:
            entity_type = self._map_spacy_label(ent.label_)
            if entity_type:
                entities.append({
                    'type': entity_type,
                    'value': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.8,  # spaCy doesn't provide confidence
                    'metadata': {'spacy_label': ent.label_}
                })
        
        return entities
    
    def _extract_pattern_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using regex patterns"""
        entities = []
        
        # Phone numbers
        for match in self.patterns['phone'].finditer(text):
            phone = match.group().strip()
            if len(re.sub(r'\D', '', phone)) >= 10:  # At least 10 digits
                entities.append({
                    'type': EntityType.PHONE,
                    'value': phone,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.9
                })
        
        # Email addresses
        for match in self.patterns['email'].finditer(text):
            entities.append({
                'type': EntityType.EMAIL,
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.95
            })
        
        # URLs
        for match in self.patterns['url'].finditer(text):
            entities.append({
                'type': EntityType.URL,
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.95
            })
        
        # Hashtags
        for match in self.patterns['hashtag'].finditer(text):
            entities.append({
                'type': EntityType.HASHTAG,
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        
        # Mentions
        for match in self.patterns['mention'].finditer(text):
            entities.append({
                'type': EntityType.MENTION,
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 1.0
            })
        
        # Dates
        for match in self.patterns['date'].finditer(text):
            entities.append({
                'type': EntityType.DATE,
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.8
            })
        
        # Times
        for match in self.patterns['time'].finditer(text):
            entities.append({
                'type': EntityType.TIME,
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.8
            })
        
        # Money
        for match in self.patterns['money'].finditer(text):
            entities.append({
                'type': EntityType.MONEY,
                'value': match.group(),
                'start': match.start(),
                'end': match.end(),
                'confidence': 0.85
            })
        
        return entities
    
    def _map_spacy_label(self, label: str) -> Optional[str]:
        """Map spaCy entity labels to our entity types"""
        mapping = {
            'PERSON': EntityType.PERSON,
            'ORG': EntityType.ORGANIZATION,
            'GPE': EntityType.LOCATION,  # Geopolitical entity
            'LOC': EntityType.LOCATION,
            'DATE': EntityType.DATE,
            'TIME': EntityType.TIME,
            'MONEY': EntityType.MONEY,
        }
        return mapping.get(label)
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on value and type"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            key = (entity['type'], entity['value'].lower())
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        """
        Extract contact information from text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with phone numbers and emails
        """
        contact_info = {
            'phones': [],
            'emails': []
        }
        
        # Extract phone numbers
        for match in self.patterns['phone'].finditer(text):
            phone = match.group().strip()
            if len(re.sub(r'\D', '', phone)) >= 10:
                contact_info['phones'].append(phone)
        
        # Extract emails
        for match in self.patterns['email'].finditer(text):
            contact_info['emails'].append(match.group())
        
        # Remove duplicates
        contact_info['phones'] = list(set(contact_info['phones']))
        contact_info['emails'] = list(set(contact_info['emails']))
        
        return contact_info
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extract location mentions from text
        
        Args:
            text: Text to analyze
            
        Returns:
            List of location names
        """
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        locations = []
        
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:
                locations.append(ent.text)
        
        # Also look for location patterns
        location_keywords = ['at', 'in', 'near', 'from', 'to']
        for i, token in enumerate(doc):
            if token.text.lower() in location_keywords and i + 1 < len(doc):
                next_token = doc[i + 1]
                if next_token.pos_ == 'PROPN':  # Proper noun
                    locations.append(next_token.text)
        
        return list(set(locations))
    
    def aggregate_entities(
        self, 
        all_entities: List[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Aggregate entities from multiple messages
        
        Args:
            all_entities: List of entity lists from messages
            
        Returns:
            Aggregated entity statistics
        """
        entity_counts = {}
        entity_types = {}
        
        # Flatten and count
        for entities in all_entities:
            for entity in entities:
                value = entity['value']
                entity_type = entity['type']
                
                # Count by value
                if value not in entity_counts:
                    entity_counts[value] = {
                        'count': 0,
                        'type': entity_type,
                        'first_seen': entity.get('start', 0)
                    }
                entity_counts[value]['count'] += 1
                
                # Count by type
                if entity_type not in entity_types:
                    entity_types[entity_type] = []
                if value not in entity_types[entity_type]:
                    entity_types[entity_type].append(value)
        
        # Sort by frequency
        top_entities = sorted(
            entity_counts.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )[:50]  # Top 50 entities
        
        return {
            'total_entities': len(entity_counts),
            'entity_types': {
                etype: len(values) 
                for etype, values in entity_types.items()
            },
            'top_entities': [
                {
                    'value': value,
                    'type': info['type'],
                    'count': info['count']
                }
                for value, info in top_entities
            ],
            'unique_phones': len(entity_types.get(EntityType.PHONE, [])),
            'unique_emails': len(entity_types.get(EntityType.EMAIL, [])),
            'unique_urls': len(entity_types.get(EntityType.URL, [])),
            'unique_people': len(entity_types.get(EntityType.PERSON, [])),
            'unique_locations': len(entity_types.get(EntityType.LOCATION, []))
        }