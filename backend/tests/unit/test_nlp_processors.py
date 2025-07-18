"""Unit tests for NLP processors."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.nlp.sentiment_analyzer import SentimentAnalyzer
from app.services.nlp.keyword_extractor import KeywordExtractor
from app.services.nlp.entity_recognizer import EntityRecognizer
from app.models.message import Message


class TestSentimentAnalyzer:
    """Test sentiment analysis functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create sentiment analyzer instance."""
        return SentimentAnalyzer()
    
    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for testing."""
        return [
            Message(
                id="1",
                conversation_id="conv1",
                sender="Alice",
                content="I love this! It's absolutely amazing and wonderful!",
                timestamp=datetime.utcnow(),
                message_type="text"
            ),
            Message(
                id="2",
                conversation_id="conv1",
                sender="Bob",
                content="This is terrible. I hate it so much. Very disappointed.",
                timestamp=datetime.utcnow(),
                message_type="text"
            ),
            Message(
                id="3",
                conversation_id="conv1",
                sender="Charlie",
                content="It's okay, I guess. Nothing special really.",
                timestamp=datetime.utcnow(),
                message_type="text"
            ),
            Message(
                id="4",
                conversation_id="conv1",
                sender="David",
                content="<Media omitted>",
                timestamp=datetime.utcnow(),
                message_type="media"
            )
        ]
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_analyze_positive_sentiment(self, analyzer):
        """Test analyzing positive sentiment."""
        positive_texts = [
            "I love this product! It's amazing!",
            "Fantastic work, really impressed!",
            "This made my day, thank you so much!",
            "Absolutely brilliant! 😊"
        ]
        
        for text in positive_texts:
            result = analyzer.analyze_text(text)
            assert result["sentiment"] == "positive"
            assert result["confidence"] > 0.7
            assert "scores" in result
            assert result["scores"]["positive"] > result["scores"]["negative"]
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_analyze_negative_sentiment(self, analyzer):
        """Test analyzing negative sentiment."""
        negative_texts = [
            "This is terrible, I hate it.",
            "Very disappointed with the service.",
            "Worst experience ever!",
            "Completely useless and frustrating 😠"
        ]
        
        for text in negative_texts:
            result = analyzer.analyze_text(text)
            assert result["sentiment"] == "negative"
            assert result["confidence"] > 0.7
            assert result["scores"]["negative"] > result["scores"]["positive"]
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_analyze_neutral_sentiment(self, analyzer):
        """Test analyzing neutral sentiment."""
        neutral_texts = [
            "The meeting is at 3 PM.",
            "Please send me the document.",
            "Okay, I understand.",
            "The weather is cloudy today."
        ]
        
        for text in neutral_texts:
            result = analyzer.analyze_text(text)
            assert result["sentiment"] == "neutral"
            assert result["scores"]["neutral"] > result["scores"]["positive"]
            assert result["scores"]["neutral"] > result["scores"]["negative"]
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_analyze_messages(self, analyzer, sample_messages):
        """Test analyzing multiple messages."""
        results = analyzer.analyze_messages(sample_messages)
        
        assert len(results) == 4
        assert results[0]["sentiment"] == "positive"  # Alice's message
        assert results[1]["sentiment"] == "negative"  # Bob's message
        assert results[2]["sentiment"] == "neutral"   # Charlie's message
        assert results[3]["sentiment"] == "neutral"   # Media message
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_analyze_empty_text(self, analyzer):
        """Test analyzing empty text."""
        result = analyzer.analyze_text("")
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 0.0
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_analyze_conversation_sentiment(self, analyzer, sample_messages):
        """Test analyzing overall conversation sentiment."""
        with patch.object(analyzer, 'analyze_messages') as mock_analyze:
            mock_analyze.return_value = [
                {"sentiment": "positive", "confidence": 0.9},
                {"sentiment": "negative", "confidence": 0.8},
                {"sentiment": "neutral", "confidence": 0.7},
                {"sentiment": "neutral", "confidence": 0.5}
            ]
            
            summary = analyzer.get_conversation_summary(sample_messages)
            
            assert "overall_sentiment" in summary
            assert "sentiment_distribution" in summary
            assert "average_confidence" in summary
            assert summary["sentiment_distribution"]["positive"] == 0.25
            assert summary["sentiment_distribution"]["negative"] == 0.25
            assert summary["sentiment_distribution"]["neutral"] == 0.5


class TestKeywordExtractor:
    """Test keyword extraction functionality."""
    
    @pytest.fixture
    def extractor(self):
        """Create keyword extractor instance."""
        return KeywordExtractor()
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_extract_keywords_from_text(self, extractor):
        """Test extracting keywords from text."""
        text = """
        Machine learning is a subset of artificial intelligence that enables 
        systems to learn and improve from experience. Deep learning models 
        use neural networks to process complex data patterns.
        """
        
        keywords = extractor.extract_from_text(text)
        
        assert len(keywords) > 0
        assert any(kw["keyword"].lower() in ["machine learning", "artificial intelligence", "deep learning"] 
                  for kw in keywords)
        
        # Check keyword structure
        for kw in keywords:
            assert "keyword" in kw
            assert "score" in kw
            assert 0 <= kw["score"] <= 1
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_extract_keywords_with_limit(self, extractor):
        """Test extracting limited number of keywords."""
        text = "Python programming language is great for data science and web development"
        
        keywords = extractor.extract_from_text(text, max_keywords=3)
        assert len(keywords) <= 3
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_extract_keywords_from_messages(self, extractor):
        """Test extracting keywords from multiple messages."""
        messages = [
            Message(
                id="1",
                conversation_id="conv1",
                sender="Alice",
                content="Let's discuss the machine learning project tomorrow",
                timestamp=datetime.utcnow(),
                message_type="text"
            ),
            Message(
                id="2",
                conversation_id="conv1",
                sender="Bob",
                content="Sure, we need to review the neural network architecture",
                timestamp=datetime.utcnow(),
                message_type="text"
            )
        ]
        
        keywords = extractor.extract_from_messages(messages)
        
        assert len(keywords) > 0
        keyword_texts = [kw["keyword"].lower() for kw in keywords]
        assert any("machine learning" in kw or "neural network" in kw for kw in keyword_texts)
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_extract_keywords_empty_text(self, extractor):
        """Test extracting keywords from empty text."""
        keywords = extractor.extract_from_text("")
        assert len(keywords) == 0
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_extract_keywords_short_text(self, extractor):
        """Test extracting keywords from very short text."""
        keywords = extractor.extract_from_text("Hello world")
        # Should handle gracefully, might return 0-2 keywords
        assert isinstance(keywords, list)
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_keyword_frequency_analysis(self, extractor):
        """Test keyword frequency analysis across messages."""
        messages = [
            Message(id="1", conversation_id="c1", sender="A", 
                   content="Python is great", timestamp=datetime.utcnow(), message_type="text"),
            Message(id="2", conversation_id="c1", sender="B", 
                   content="I love Python programming", timestamp=datetime.utcnow(), message_type="text"),
            Message(id="3", conversation_id="c1", sender="A", 
                   content="Python for data science", timestamp=datetime.utcnow(), message_type="text"),
        ]
        
        with patch.object(extractor, 'extract_from_messages') as mock_extract:
            mock_extract.return_value = [
                {"keyword": "Python", "score": 0.9},
                {"keyword": "programming", "score": 0.7},
                {"keyword": "data science", "score": 0.8}
            ]
            
            analysis = extractor.get_keyword_trends(messages)
            assert "top_keywords" in analysis
            assert "keyword_frequency" in analysis


class TestEntityRecognizer:
    """Test entity recognition functionality."""
    
    @pytest.fixture
    def recognizer(self):
        """Create entity recognizer instance."""
        return EntityRecognizer()
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_recognize_person_entities(self, recognizer):
        """Test recognizing person names."""
        text = "John Smith and Mary Johnson will meet tomorrow."
        
        entities = recognizer.extract_entities(text)
        person_entities = [e for e in entities if e["type"] == "PERSON"]
        
        assert len(person_entities) >= 2
        entity_texts = [e["text"] for e in person_entities]
        assert any("John" in text or "Smith" in text for text in entity_texts)
        assert any("Mary" in text or "Johnson" in text for text in entity_texts)
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_recognize_location_entities(self, recognizer):
        """Test recognizing locations."""
        text = "The conference will be held in New York City at the Manhattan Convention Center."
        
        entities = recognizer.extract_entities(text)
        location_entities = [e for e in entities if e["type"] == "LOCATION"]
        
        assert len(location_entities) >= 1
        entity_texts = [e["text"] for e in location_entities]
        assert any("New York" in text or "Manhattan" in text for text in entity_texts)
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_recognize_organization_entities(self, recognizer):
        """Test recognizing organizations."""
        text = "Google and Microsoft announced a partnership with OpenAI."
        
        entities = recognizer.extract_entities(text)
        org_entities = [e for e in entities if e["type"] == "ORGANIZATION"]
        
        assert len(org_entities) >= 2
        entity_texts = [e["text"] for e in org_entities]
        assert any("Google" in text for text in entity_texts)
        assert any("Microsoft" in text for text in entity_texts)
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_recognize_date_time_entities(self, recognizer):
        """Test recognizing dates and times."""
        text = "Let's meet tomorrow at 3:30 PM or next Monday morning."
        
        entities = recognizer.extract_entities(text)
        datetime_entities = [e for e in entities if e["type"] in ["DATE", "TIME"]]
        
        assert len(datetime_entities) >= 2
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_recognize_entities_from_messages(self, recognizer):
        """Test recognizing entities from multiple messages."""
        messages = [
            Message(
                id="1",
                conversation_id="conv1",
                sender="Alice",
                content="I'll meet John at Starbucks in Seattle tomorrow at 2 PM",
                timestamp=datetime.utcnow(),
                message_type="text"
            ),
            Message(
                id="2",
                conversation_id="conv1",
                sender="Bob",
                content="Great! Microsoft headquarters is nearby",
                timestamp=datetime.utcnow(),
                message_type="text"
            )
        ]
        
        all_entities = recognizer.extract_from_messages(messages)
        
        assert len(all_entities) > 0
        
        # Check for different entity types
        entity_types = set(e["type"] for e in all_entities)
        assert "PERSON" in entity_types
        assert "LOCATION" in entity_types or "GPE" in entity_types
        assert "ORGANIZATION" in entity_types
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_recognize_entities_empty_text(self, recognizer):
        """Test entity recognition on empty text."""
        entities = recognizer.extract_entities("")
        assert len(entities) == 0
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_entity_aggregation(self, recognizer):
        """Test entity aggregation across conversation."""
        messages = [
            Message(id="1", conversation_id="c1", sender="A",
                   content="John works at Google", timestamp=datetime.utcnow(), message_type="text"),
            Message(id="2", conversation_id="c1", sender="B",
                   content="Yes, John is in the New York office", timestamp=datetime.utcnow(), message_type="text"),
            Message(id="3", conversation_id="c1", sender="A",
                   content="Google has many offices", timestamp=datetime.utcnow(), message_type="text"),
        ]
        
        with patch.object(recognizer, 'extract_from_messages') as mock_extract:
            mock_extract.return_value = [
                {"text": "John", "type": "PERSON", "start": 0, "end": 4},
                {"text": "Google", "type": "ORGANIZATION", "start": 15, "end": 21},
                {"text": "John", "type": "PERSON", "start": 5, "end": 9},
                {"text": "New York", "type": "LOCATION", "start": 20, "end": 28},
                {"text": "Google", "type": "ORGANIZATION", "start": 0, "end": 6}
            ]
            
            summary = recognizer.get_entity_summary(messages)
            
            assert "entities_by_type" in summary
            assert "most_mentioned" in summary
            assert summary["entities_by_type"]["PERSON"] == ["John"]
            assert summary["entities_by_type"]["ORGANIZATION"] == ["Google"]
            assert summary["most_mentioned"][0]["entity"] in ["John", "Google"]
            assert summary["most_mentioned"][0]["count"] == 2
    
    @pytest.mark.unit
    @pytest.mark.nlp
    def test_entity_confidence_scores(self, recognizer):
        """Test that entities include confidence scores."""
        text = "Apple Inc. is headquartered in Cupertino, California."
        
        entities = recognizer.extract_entities(text)
        
        for entity in entities:
            assert "text" in entity
            assert "type" in entity
            assert "start" in entity
            assert "end" in entity
            # Confidence might be optional depending on implementation
            if "confidence" in entity:
                assert 0 <= entity["confidence"] <= 1