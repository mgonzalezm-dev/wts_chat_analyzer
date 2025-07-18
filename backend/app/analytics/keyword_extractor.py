"""
Keyword extraction module for identifying important terms and topics
"""

import asyncio
from typing import List, Dict, Any, Tuple, Optional
import logging
from collections import Counter
import re
import math
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.util import ngrams

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
except:
    logger.warning("Failed to download NLTK data")


class KeywordExtractor:
    """
    Extract keywords and key phrases from messages using:
    - TF-IDF
    - Frequency analysis
    - N-gram extraction
    """
    
    def __init__(self, language: str = 'english'):
        """
        Initialize keyword extractor
        
        Args:
            language: Language for stopwords
        """
        self.language = language
        self._init_stopwords()
        self.tfidf_vectorizer = None
    
    def _init_stopwords(self):
        """Initialize stopwords list"""
        try:
            self.stopwords = set(stopwords.words(self.language))
        except:
            # Fallback to basic English stopwords
            self.stopwords = {
                'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
                'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
                'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                'what', 'which', 'who', 'whom', 'this', 'that', 'these',
                'those', 'am', 'is', 'are', 'was', 'were', 'been', 'being',
                'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
                'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
                'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
                'against', 'between', 'into', 'through', 'during', 'before',
                'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in',
                'out', 'on', 'off', 'over', 'under', 'again', 'further',
                'then', 'once'
            }
        
        # Add common WhatsApp-specific stopwords
        self.stopwords.update({
            'media', 'omitted', 'message', 'deleted', 'https', 'http',
            'www', 'com', 'whatsapp', 'sent', 'received', 'forwarded'
        })
    
    async def extract_keywords(
        self, 
        messages: List[str], 
        max_keywords: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Extract keywords from messages
        
        Args:
            messages: List of message texts
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords with scores
        """
        if not messages:
            return []
        
        # Filter out empty messages
        messages = [msg for msg in messages if msg and len(msg.strip()) > 0]
        if not messages:
            return []
        
        # Run extraction in thread pool
        loop = asyncio.get_event_loop()
        keywords = await loop.run_in_executor(
            None,
            self._extract_keywords_sync,
            messages,
            max_keywords
        )
        
        return keywords
    
    def _extract_keywords_sync(
        self, 
        messages: List[str], 
        max_keywords: int
    ) -> List[Dict[str, Any]]:
        """Synchronous keyword extraction"""
        # Combine all messages
        combined_text = ' '.join(messages)
        
        # Extract using multiple methods
        tfidf_keywords = self._extract_tfidf_keywords(messages, max_keywords)
        freq_keywords = self._extract_frequency_keywords(combined_text, max_keywords)
        
        # Combine and rank
        all_keywords = {}
        
        # Add TF-IDF keywords
        for kw in tfidf_keywords:
            all_keywords[kw['word']] = {
                'word': kw['word'],
                'tfidf_score': kw['score'],
                'frequency': 0,
                'combined_score': kw['score']
            }
        
        # Add frequency keywords
        for kw in freq_keywords:
            if kw['word'] in all_keywords:
                all_keywords[kw['word']]['frequency'] = kw['count']
                # Combine scores
                all_keywords[kw['word']]['combined_score'] = (
                    all_keywords[kw['word']]['tfidf_score'] * 0.7 +
                    kw['normalized_score'] * 0.3
                )
            else:
                all_keywords[kw['word']] = {
                    'word': kw['word'],
                    'tfidf_score': 0,
                    'frequency': kw['count'],
                    'combined_score': kw['normalized_score'] * 0.3
                }
        
        # Sort by combined score
        sorted_keywords = sorted(
            all_keywords.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:max_keywords]
        
        return sorted_keywords
    
    def _extract_tfidf_keywords(
        self, 
        messages: List[str], 
        max_keywords: int
    ) -> List[Dict[str, Any]]:
        """Extract keywords using TF-IDF"""
        try:
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=max_keywords * 2,
                stop_words=list(self.stopwords),
                ngram_range=(1, 2),  # Include bigrams
                min_df=2,  # Minimum document frequency
                max_df=0.8  # Maximum document frequency
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform(messages)
            
            # Get feature names
            feature_names = vectorizer.get_feature_names_out()
            
            # Calculate average TF-IDF scores
            avg_scores = tfidf_matrix.mean(axis=0).A1
            
            # Create keyword list
            keywords = []
            for idx, score in enumerate(avg_scores):
                if score > 0:
                    keywords.append({
                        'word': feature_names[idx],
                        'score': float(score)
                    })
            
            # Sort by score
            keywords.sort(key=lambda x: x['score'], reverse=True)
            
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"TF-IDF extraction failed: {e}")
            return []
    
    def _extract_frequency_keywords(
        self, 
        text: str, 
        max_keywords: int
    ) -> List[Dict[str, Any]]:
        """Extract keywords based on frequency"""
        # Tokenize
        tokens = self._tokenize(text.lower())
        
        # Filter tokens
        filtered_tokens = [
            token for token in tokens
            if len(token) > 2 and token not in self.stopwords
            and not token.isdigit()
        ]
        
        # Count frequencies
        word_freq = Counter(filtered_tokens)
        
        # Get most common
        most_common = word_freq.most_common(max_keywords)
        
        # Normalize scores
        max_count = most_common[0][1] if most_common else 1
        
        keywords = []
        for word, count in most_common:
            keywords.append({
                'word': word,
                'count': count,
                'normalized_score': count / max_count
            })
        
        return keywords
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text"""
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Tokenize
        try:
            tokens = word_tokenize(text)
        except:
            # Fallback tokenization
            tokens = text.split()
        
        return tokens
    
    async def extract_ngrams(
        self, 
        messages: List[str], 
        n: int = 2, 
        max_ngrams: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Extract n-grams (phrases) from messages
        
        Args:
            messages: List of message texts
            n: N-gram size (2 for bigrams, 3 for trigrams)
            max_ngrams: Maximum number of n-grams to return
            
        Returns:
            List of n-grams with frequencies
        """
        if not messages:
            return []
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        ngrams_list = await loop.run_in_executor(
            None,
            self._extract_ngrams_sync,
            messages,
            n,
            max_ngrams
        )
        
        return ngrams_list
    
    def _extract_ngrams_sync(
        self, 
        messages: List[str], 
        n: int, 
        max_ngrams: int
    ) -> List[Dict[str, Any]]:
        """Synchronous n-gram extraction"""
        all_ngrams = []
        
        for message in messages:
            # Tokenize
            tokens = self._tokenize(message.lower())
            
            # Filter tokens
            filtered_tokens = [
                token for token in tokens
                if len(token) > 1 and token not in self.stopwords
            ]
            
            # Generate n-grams
            if len(filtered_tokens) >= n:
                message_ngrams = list(ngrams(filtered_tokens, n))
                all_ngrams.extend(message_ngrams)
        
        # Count frequencies
        ngram_freq = Counter(all_ngrams)
        
        # Get most common
        most_common = ngram_freq.most_common(max_ngrams)
        
        # Format results
        results = []
        for ngram_tuple, count in most_common:
            phrase = ' '.join(ngram_tuple)
            results.append({
                'phrase': phrase,
                'count': count,
                'words': list(ngram_tuple)
            })
        
        return results
    
    async def extract_topics(
        self, 
        messages: List[str], 
        num_topics: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract topics from messages using simple clustering
        
        Args:
            messages: List of message texts
            num_topics: Number of topics to extract
            
        Returns:
            List of topics with associated keywords
        """
        if not messages or len(messages) < num_topics:
            return []
        
        # Extract keywords for topic modeling
        keywords = await self.extract_keywords(messages, max_keywords=50)
        
        # Group keywords into topics (simplified approach)
        topics = []
        keywords_per_topic = len(keywords) // num_topics
        
        for i in range(num_topics):
            start_idx = i * keywords_per_topic
            end_idx = start_idx + keywords_per_topic
            
            topic_keywords = keywords[start_idx:end_idx]
            if topic_keywords:
                # Generate topic name from top keywords
                topic_name = ', '.join([kw['word'] for kw in topic_keywords[:3]])
                
                topics.append({
                    'id': i,
                    'name': topic_name,
                    'keywords': topic_keywords,
                    'score': sum(kw.get('combined_score', 0) for kw in topic_keywords)
                })
        
        return topics
    
    def calculate_keyword_trends(
        self, 
        messages_by_date: Dict[str, List[str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate keyword trends over time
        
        Args:
            messages_by_date: Dictionary mapping dates to message lists
            
        Returns:
            Dictionary mapping keywords to trend data
        """
        keyword_trends = {}
        
        # Extract keywords for each date
        for date, messages in sorted(messages_by_date.items()):
            if not messages:
                continue
            
            # Extract keywords for this date
            keywords = self._extract_frequency_keywords(
                ' '.join(messages), 
                max_keywords=20
            )
            
            # Update trends
            for kw in keywords:
                word = kw['word']
                if word not in keyword_trends:
                    keyword_trends[word] = []
                
                keyword_trends[word].append({
                    'date': date,
                    'count': kw['count'],
                    'score': kw['normalized_score']
                })
        
        # Filter to keep only trending keywords
        trending_keywords = {}
        for word, trend_data in keyword_trends.items():
            if len(trend_data) >= 3:  # Appears in at least 3 time periods
                trending_keywords[word] = trend_data
        
        return trending_keywords