"""
Sentiment analysis module
"""

import asyncio
from typing import List, Dict, Any
import logging
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from app.models.conversation import Message
from app.models.analytics import SentimentLabel

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('vader_lexicon', quiet=True)
except:
    logger.warning("Failed to download NLTK vader_lexicon")


class SentimentAnalyzer:
    """
    Sentiment analysis for messages
    """
    
    def __init__(self):
        """Initialize sentiment analyzer"""
        try:
            self.sia = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Failed to initialize SentimentIntensityAnalyzer: {e}")
            self.sia = None
    
    async def analyze_message(self, message: Message) -> Dict[str, Any]:
        """
        Analyze sentiment of a single message
        
        Args:
            message: Message to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        if not message.content:
            return self._empty_sentiment()
        
        # Run analysis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            self._analyze_text, 
            message.content
        )
        
        return result
    
    async def analyze_messages_batch(
        self, 
        messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple messages
        
        Args:
            messages: List of messages
            
        Returns:
            List of sentiment results
        """
        tasks = [self.analyze_message(msg) for msg in messages]
        results = await asyncio.gather(*tasks)
        return results
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Perform sentiment analysis on text
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment scores and labels
        """
        if not text:
            return self._empty_sentiment()
        
        # Use VADER sentiment analyzer if available
        if self.sia:
            scores = self.sia.polarity_scores(text)
            
            # Determine sentiment label
            compound = scores['compound']
            if compound >= 0.5:
                label = SentimentLabel.VERY_POSITIVE
            elif compound >= 0.1:
                label = SentimentLabel.POSITIVE
            elif compound <= -0.5:
                label = SentimentLabel.VERY_NEGATIVE
            elif compound <= -0.1:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL
            
            # Calculate emotion scores
            emotion_scores = {
                'joy': max(0, scores['pos']),
                'anger': max(0, scores['neg'] * 0.5),
                'fear': max(0, scores['neg'] * 0.3),
                'sadness': max(0, scores['neg'] * 0.2),
                'surprise': max(0, abs(compound) * 0.3 if abs(compound) > 0.5 else 0),
                'neutral': scores['neu']
            }
            
            return {
                'polarity': compound,
                'subjectivity': self._calculate_subjectivity(text),
                'sentiment_label': label,
                'emotion_scores': emotion_scores,
                'raw_scores': {
                    'positive': scores['pos'],
                    'negative': scores['neg'],
                    'neutral': scores['neu'],
                    'compound': scores['compound']
                }
            }
        
        # Fallback to TextBlob
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Determine sentiment label
            if polarity >= 0.5:
                label = SentimentLabel.VERY_POSITIVE
            elif polarity >= 0.1:
                label = SentimentLabel.POSITIVE
            elif polarity <= -0.5:
                label = SentimentLabel.VERY_NEGATIVE
            elif polarity <= -0.1:
                label = SentimentLabel.NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL
            
            # Estimate emotion scores
            emotion_scores = {
                'joy': max(0, polarity) if polarity > 0 else 0,
                'anger': max(0, -polarity * 0.5) if polarity < 0 else 0,
                'fear': max(0, -polarity * 0.3) if polarity < 0 else 0,
                'sadness': max(0, -polarity * 0.2) if polarity < 0 else 0,
                'surprise': 0.1 if abs(polarity) > 0.7 else 0,
                'neutral': 1 - abs(polarity)
            }
            
            return {
                'polarity': polarity,
                'subjectivity': subjectivity,
                'sentiment_label': label,
                'emotion_scores': emotion_scores,
                'raw_scores': {
                    'polarity': polarity,
                    'subjectivity': subjectivity
                }
            }
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return self._empty_sentiment()
    
    def _calculate_subjectivity(self, text: str) -> float:
        """
        Calculate subjectivity score
        
        Args:
            text: Text to analyze
            
        Returns:
            Subjectivity score (0-1)
        """
        try:
            blob = TextBlob(text)
            return blob.sentiment.subjectivity
        except:
            # Fallback: estimate based on certain patterns
            subjective_words = [
                'think', 'believe', 'feel', 'opinion', 'seems',
                'maybe', 'probably', 'possibly', 'perhaps', 'might',
                'love', 'hate', 'like', 'dislike', 'prefer',
                'beautiful', 'ugly', 'good', 'bad', 'best', 'worst'
            ]
            
            text_lower = text.lower()
            word_count = len(text.split())
            if word_count == 0:
                return 0.0
            
            subjective_count = sum(1 for word in subjective_words if word in text_lower)
            return min(1.0, subjective_count / word_count * 5)  # Scale factor
    
    def _empty_sentiment(self) -> Dict[str, Any]:
        """Return empty sentiment result"""
        return {
            'polarity': 0.0,
            'subjectivity': 0.0,
            'sentiment_label': SentimentLabel.NEUTRAL,
            'emotion_scores': {
                'joy': 0.0,
                'anger': 0.0,
                'fear': 0.0,
                'sadness': 0.0,
                'surprise': 0.0,
                'neutral': 1.0
            },
            'raw_scores': {}
        }
    
    def calculate_conversation_sentiment(
        self, 
        sentiments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate sentiment for a conversation
        
        Args:
            sentiments: List of sentiment results
            
        Returns:
            Aggregate sentiment statistics
        """
        if not sentiments:
            return {
                'average_polarity': 0.0,
                'average_subjectivity': 0.0,
                'dominant_sentiment': SentimentLabel.NEUTRAL,
                'sentiment_distribution': {},
                'emotion_distribution': {}
            }
        
        # Calculate averages
        polarities = [s['polarity'] for s in sentiments]
        subjectivities = [s['subjectivity'] for s in sentiments]
        
        avg_polarity = sum(polarities) / len(polarities)
        avg_subjectivity = sum(subjectivities) / len(subjectivities)
        
        # Calculate sentiment distribution
        sentiment_counts = {}
        for s in sentiments:
            label = s['sentiment_label']
            sentiment_counts[label] = sentiment_counts.get(label, 0) + 1
        
        total = len(sentiments)
        sentiment_distribution = {
            label: count / total 
            for label, count in sentiment_counts.items()
        }
        
        # Find dominant sentiment
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate emotion distribution
        emotion_totals = {
            'joy': 0.0,
            'anger': 0.0,
            'fear': 0.0,
            'sadness': 0.0,
            'surprise': 0.0,
            'neutral': 0.0
        }
        
        for s in sentiments:
            for emotion, score in s.get('emotion_scores', {}).items():
                emotion_totals[emotion] += score
        
        emotion_distribution = {
            emotion: total / len(sentiments)
            for emotion, total in emotion_totals.items()
        }
        
        return {
            'average_polarity': avg_polarity,
            'average_subjectivity': avg_subjectivity,
            'dominant_sentiment': dominant_sentiment,
            'sentiment_distribution': sentiment_distribution,
            'emotion_distribution': emotion_distribution,
            'positive_ratio': sum(1 for p in polarities if p > 0.1) / total,
            'negative_ratio': sum(1 for p in polarities if p < -0.1) / total,
            'neutral_ratio': sum(1 for p in polarities if -0.1 <= p <= 0.1) / total
        }