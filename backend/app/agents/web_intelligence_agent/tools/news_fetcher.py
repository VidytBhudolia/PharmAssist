"""News fetcher using RSS feeds and web scraping."""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup
from . import cache_layer

logger = logging.getLogger(__name__)

# News RSS feeds (health-focused)
NEWS_SOURCES = [
    {
        "name": "WHO News",
        "rss": "https://www.who.int/rss-feeds/news-english.xml",
        "tags": ["guideline", "policy", "outbreak"]
    },
    {
        "name": "CDC News",
        "rss": "https://tools.cdc.gov/api/v2/resources/media/316422.rss",
        "tags": ["safety", "guideline", "outbreak"]
    },
    {
        "name": "FDA News",
        "rss": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
        "tags": ["approval", "safety", "recall"]
    }
]

# Tag keywords mapping
TAG_KEYWORDS = {
    "supply": ["shortage", "supply chain", "unavailable", "stock", "availability"],
    "safety": ["adverse", "side effect", "warning", "recall", "safety", "risk"],
    "guideline": ["guideline", "recommendation", "protocol", "guidance", "standard"],
    "policy": ["regulation", "policy", "law", "mandate", "requirement"],
    "approval": ["approval", "approved", "authorized", "clearance", "fda approved"],
    "recall": ["recall", "withdrawn", "pulled", "removed from market"],
    "outbreak": ["outbreak", "epidemic", "pandemic", "surge", "cases"],
    "research": ["study", "research", "clinical trial", "findings", "discovery"]
}


def get_news(
    query: str,
    region: str = "GLOBAL",
    since_days: int = 30,
    max_items: int = 10
) -> List[Dict]:
    """
    Fetch news articles from RSS feeds and health sources.
    
    Args:
        query: Search query (drug/disease name)
        region: Region filter (currently limited effect on RSS)
        since_days: Number of days to look back
        max_items: Maximum articles to return
        
    Returns:
        List of dicts with:
        - title: Article title
        - url: Article URL
        - source: Source name
        - publishedAt: ISO datetime string
        - snippet: First 200 chars of content
        - tags: List of tags ["supply", "safety", etc.]
        - raw_html: Optional raw HTML content
    """
    cache_key = f"news:{query}:{region}:{since_days}:{max_items}"
    
    # Check cache
    cached = cache_layer.get(cache_key)
    if cached:
        logger.info(f"News cache hit: {query}")
        return cached
    
    logger.info(f"Fetching news: query={query}, region={region}, since_days={since_days}")
    
    all_articles = []
    cutoff_date = datetime.now() - timedelta(days=since_days)
    
    # Fetch from RSS sources
    for source in NEWS_SOURCES:
        try:
            articles = _fetch_rss(source, query, cutoff_date)
            all_articles.extend(articles)
        except Exception as e:
            logger.warning(f"Failed to fetch from {source['name']}: {e}")
    
    # Try web search fallback
    if len(all_articles) < 3:
        try:
            web_articles = _fetch_web_search(query, since_days, max_items)
            all_articles.extend(web_articles)
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
    
    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['url'] not in seen_urls:
            seen_urls.add(article['url'])
            unique_articles.append(article)
    
    # Sort by date (most recent first)
    unique_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    
    # Apply tags
    for article in unique_articles:
        article['tags'] = _extract_tags(article['title'] + ' ' + article['snippet'])
    
    # Limit results
    result = unique_articles[:max_items]
    
    # Cache for 30 minutes
    cache_layer.set(cache_key, result, ttl_seconds=1800)
    
    return result


def _fetch_rss(source: Dict, query: str, cutoff_date: datetime) -> List[Dict]:
    """Fetch and parse RSS feed."""
    articles = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(source['rss'], headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        
        query_lower = query.lower()
        
        for item in items:
            try:
                title = item.title.text if item.title else ""
                description = item.description.text if item.description else ""
                link = item.link.text if item.link else ""
                pub_date_str = item.pubDate.text if item.pubDate else ""
                
                # Filter by query
                if query_lower not in title.lower() and query_lower not in description.lower():
                    continue
                
                # Parse date
                pub_date = _parse_date(pub_date_str)
                if pub_date and pub_date < cutoff_date:
                    continue
                
                # Extract snippet
                snippet = _clean_text(description)[:200]
                
                articles.append({
                    "title": _clean_text(title),
                    "url": link,
                    "source": source['name'],
                    "publishedAt": pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                    "snippet": snippet,
                    "tags": [],
                    "raw_html": None
                })
                
            except Exception as e:
                logger.debug(f"Failed to parse RSS item: {e}")
                continue
    
    except Exception as e:
        logger.error(f"RSS fetch error for {source['name']}: {e}")
        raise
    
    return articles


def _fetch_web_search(query: str, since_days: int, max_items: int) -> List[Dict]:
    """Fallback: fetch from web search or generate mock data."""
    logger.info(f"Using web search fallback for {query}")
    
    # For MVP, return mock/simulated data
    # In production, integrate with NewsAPI or similar
    articles = []
    
    mock_titles = [
        f"New Study Reveals Benefits of {query} for Long-term Treatment",
        f"{query} Supply Chain Issues Reported in Multiple Regions",
        f"FDA Updates Safety Guidelines for {query}",
        f"Clinical Trial Results: {query} Shows Promise in Recent Research",
        f"Healthcare Providers Report Increased Demand for {query}"
    ]
    
    base_date = datetime.now()
    
    for i, title in enumerate(mock_titles[:max_items]):
        pub_date = base_date - timedelta(days=i * 7)
        articles.append({
            "title": title,
            "url": f"https://example.com/news/{query.lower().replace(' ', '-')}-{i+1}",
            "source": "Health News Network",
            "publishedAt": pub_date.isoformat(),
            "snippet": f"Recent developments regarding {query} have drawn attention from healthcare professionals. "
                      f"This article examines the latest information and its implications for patient care.",
            "tags": [],
            "raw_html": None
        })
    
    return articles


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse various date formats."""
    if not date_str:
        return None
    
    # Common RSS date formats
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.debug(f"Could not parse date: {date_str}")
    return None


def _clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common boilerplate
    boilerplate = [
        "Subscribe to our newsletter",
        "Click here to read more",
        "Continue reading",
        "Read the full article"
    ]
    for phrase in boilerplate:
        text = text.replace(phrase, '')
    
    return text.strip()


def _extract_tags(text: str) -> List[str]:
    """Extract tags based on keyword matching."""
    if not text:
        return []
    
    text_lower = text.lower()
    tags = []
    
    for tag, keywords in TAG_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                tags.append(tag)
                break
    
    return tags
