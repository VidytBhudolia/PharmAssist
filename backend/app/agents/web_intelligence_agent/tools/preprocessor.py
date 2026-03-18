"""Text preprocessing and cleaning utilities."""

import logging
import re
from typing import List, Dict
import unicodedata

logger = logging.getLogger(__name__)


def clean_items(news_items: List[Dict], forum_items: List[Dict]) -> Dict:
    """
    Clean and deduplicate news and forum items.
    
    Args:
        news_items: List of news article dicts
        forum_items: List of forum snippet dicts
        
    Returns:
        Dict with cleaned "news" and "forums" lists
    """
    logger.info(f"Preprocessing {len(news_items)} news items and {len(forum_items)} forum items")
    
    cleaned_news = []
    for item in news_items:
        try:
            cleaned = _clean_news_item(item)
            if cleaned:
                cleaned_news.append(cleaned)
        except Exception as e:
            logger.warning(f"Failed to clean news item: {e}")
    
    cleaned_forums = []
    for item in forum_items:
        try:
            cleaned = _clean_forum_item(item)
            if cleaned:
                cleaned_forums.append(cleaned)
        except Exception as e:
            logger.warning(f"Failed to clean forum item: {e}")
    
    # Deduplicate
    cleaned_news = _deduplicate_news(cleaned_news)
    cleaned_forums = _deduplicate_forums(cleaned_forums)
    
    logger.info(f"Cleaned: {len(cleaned_news)} news, {len(cleaned_forums)} forum items")
    
    return {
        "news": cleaned_news,
        "forums": cleaned_forums
    }


def _clean_news_item(item: Dict) -> Dict:
    """Clean a single news item."""
    cleaned = item.copy()
    
    # Clean title
    if 'title' in cleaned:
        cleaned['title'] = _clean_text(cleaned['title'])
    
    # Clean snippet
    if 'snippet' in cleaned:
        cleaned['snippet'] = _clean_text(cleaned['snippet'])
        cleaned['snippet'] = _remove_boilerplate(cleaned['snippet'])
    
    # Validate required fields
    if not cleaned.get('title') or not cleaned.get('url'):
        return None
    
    return cleaned


def _clean_forum_item(item: Dict) -> Dict:
    """Clean a single forum item."""
    cleaned = item.copy()
    
    # Clean quote
    if 'quote' in cleaned:
        cleaned['quote'] = _clean_text(cleaned['quote'])
        
        # Enforce 25-word limit
        words = cleaned['quote'].split()
        if len(words) > 25:
            cleaned['quote'] = ' '.join(words[:25])
    
    # Validate
    if not cleaned.get('quote') or not cleaned.get('url'):
        return None
    
    return cleaned


def _clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    - Remove HTML tags
    - Normalize Unicode
    - Remove excessive whitespace
    - Remove control characters
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize Unicode (NFD decomposition + filter)
    text = unicodedata.normalize('NFKD', text)
    
    # Remove control characters
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t ')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Trim
    text = text.strip()
    
    return text


def _remove_boilerplate(text: str) -> str:
    """Remove common boilerplate phrases from text."""
    boilerplate_patterns = [
        r'Subscribe to our newsletter',
        r'Click here to read more',
        r'Continue reading',
        r'Read the full article',
        r'Sign up for free',
        r'This article was originally published',
        r'For more information visit',
        r'Follow us on',
        r'Share this article',
        r'Print this article',
        r'\[Continue reading\]',
        r'\[Read more\]',
    ]
    
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up resulting whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def _deduplicate_news(items: List[Dict]) -> List[Dict]:
    """Remove duplicate news items based on URL and title similarity."""
    if not items:
        return []
    
    seen_urls = set()
    seen_titles = set()
    unique = []
    
    for item in items:
        url = item.get('url', '')
        title = item.get('title', '').lower()
        
        # Check URL
        if url in seen_urls:
            continue
        
        # Check title similarity (exact match for now)
        if title in seen_titles:
            continue
        
        seen_urls.add(url)
        seen_titles.add(title)
        unique.append(item)
    
    return unique


def _deduplicate_forums(items: List[Dict]) -> List[Dict]:
    """Remove duplicate forum items based on quote similarity."""
    if not items:
        return []
    
    seen_quotes = set()
    unique = []
    
    for item in items:
        quote = item.get('quote', '').lower()
        
        # Exact match check
        if quote in seen_quotes:
            continue
        
        seen_quotes.add(quote)
        unique.append(item)
    
    return unique


def detect_language(text: str) -> str:
    """
    Simple language detection (English vs non-English).
    
    Returns:
        "en" for English, "other" for non-English
    """
    if not text:
        return "unknown"
    
    # Simple heuristic: check for common English words
    common_english = [
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are',
        'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'must', 'can', 'of', 'to', 'in', 'for', 'with'
    ]
    
    words = text.lower().split()
    if not words:
        return "unknown"
    
    english_count = sum(1 for word in words if word in common_english)
    english_ratio = english_count / len(words)
    
    return "en" if english_ratio > 0.1 else "other"
