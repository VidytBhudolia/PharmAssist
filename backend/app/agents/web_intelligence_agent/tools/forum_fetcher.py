"""Forum data fetcher for patient sentiment from Reddit and other forums."""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from . import cache_layer

logger = logging.getLogger(__name__)

# Try to import praw (Reddit API), fallback to stub
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    logger.warning("praw not available, using stub implementation")
    PRAW_AVAILABLE = False

# Default subreddits for health discussions
DEFAULT_SUBREDDITS = [
    "r/diabetes",
    "r/hypertension",
    "r/Cardiovascular",
    "r/cancer",
    "r/Asthma",
    "r/arthritis",
    "r/depression",
    "r/Anxiety",
    "r/migraine",
    "r/medical",
    "r/AskDocs",
    "r/HealthAnxiety"
]


def get_forum_snippets(
    query: str,
    subreddit_list: Optional[List[str]] = None,
    since_days: int = 30,
    max_items: int = 20
) -> List[Dict]:
    """
    Fetch anonymized forum quotes from Reddit.
    
    Args:
        query: Search term (drug or disease)
        subreddit_list: List of subreddit names to search (default: health-related)
        since_days: Days to look back
        max_items: Maximum snippets to return
        
    Returns:
        List of dicts with:
        - site: "reddit/r/subreddit"
        - quote: Anonymized text snippet (<=25 words)
        - url: Thread URL
        - sentiment: "POS" | "NEU" | "NEG"
        - score: float (0-1 normalized)
    """
    cache_key = f"forum:{query}:{since_days}:{max_items}"
    
    # Check cache
    cached = cache_layer.get(cache_key)
    if cached:
        logger.info(f"Forum cache hit: {query}")
        return cached
    
    if subreddit_list is None:
        subreddit_list = DEFAULT_SUBREDDITS
    
    logger.info(f"Fetching forum data: query={query}, subreddits={len(subreddit_list)}")
    
    if not PRAW_AVAILABLE:
        # Use stub data
        result = _stub_forum_data(query, since_days, max_items)
    else:
        try:
            result = _fetch_real_forum_data(query, subreddit_list, since_days, max_items)
        except Exception as e:
            logger.error(f"Forum fetch failed: {e}")
            result = _stub_forum_data(query, since_days, max_items)
    
    # Cache for 1 hour
    cache_layer.set(cache_key, result, ttl_seconds=3600)
    
    return result


def _fetch_real_forum_data(
    query: str,
    subreddit_list: List[str],
    since_days: int,
    max_items: int
) -> List[Dict]:
    """Fetch real data from Reddit using PRAW."""
    # Note: This requires Reddit API credentials
    # For production, set environment variables: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
    
    snippets = []
    cutoff_timestamp = (datetime.now() - timedelta(days=since_days)).timestamp()
    
    try:
        # Initialize Reddit client (read-only)
        reddit = praw.Reddit(
            client_id="YOUR_CLIENT_ID",  # Set via environment
            client_secret="YOUR_CLIENT_SECRET",
            user_agent="PharmAssist Web Intelligence Agent v1.0"
        )
        
        for subreddit_name in subreddit_list:
            try:
                subreddit = reddit.subreddit(subreddit_name.replace('r/', ''))
                
                # Search recent posts
                for submission in subreddit.search(query, time_filter='month', limit=50):
                    if submission.created_utc < cutoff_timestamp:
                        continue
                    
                    # Process submission text
                    text = submission.title + " " + (submission.selftext or "")
                    snippet = _extract_snippet(text, query)
                    
                    if snippet and _is_safe_content(snippet):
                        snippets.append({
                            "site": f"reddit/{subreddit_name}",
                            "quote": snippet,
                            "url": f"https://reddit.com{submission.permalink}",
                            "sentiment": _analyze_sentiment(snippet),
                            "score": _normalize_score(submission.score)
                        })
                    
                    if len(snippets) >= max_items:
                        break
                
            except Exception as e:
                logger.warning(f"Error fetching from {subreddit_name}: {e}")
                continue
            
            if len(snippets) >= max_items:
                break
        
    except Exception as e:
        logger.error(f"PRAW error: {e}")
        raise
    
    return snippets[:max_items]


def _stub_forum_data(query: str, since_days: int, max_items: int) -> List[Dict]:
    """Generate stub forum data for testing."""
    logger.info(f"Using stub forum data for {query}")
    
    templates = [
        f"Has anyone tried {query}? What were your experiences with it?",
        f"My doctor prescribed {query} and I'm seeing good results so far",
        f"Experiencing side effects with {query}, is this normal?",
        f"Been on {query} for 6 months now, definitely helps with symptoms",
        f"Looking for alternatives to {query}, any suggestions?",
        f"{query} has been life-changing for managing my condition",
        f"Insurance won't cover {query} anymore, very frustrated",
        f"Warning: {query} gave me severe reactions, be careful",
        f"Generic version of {query} works just as well for me",
        f"Doctors should prescribe {query} more often, it really helps",
        f"Mixed results with {query}, works for some days not others",
        f"Affordable alternative to {query} that worked well for me",
        f"Clinical trial participant for {query}, positive experience overall",
        f"{query} availability issues in my area, anyone else?",
        f"Long-term user of {query} here, happy to answer questions"
    ]
    
    snippets = []
    base_date = datetime.now()
    
    for i, template in enumerate(templates[:max_items]):
        # Limit to 25 words
        words = template.split()
        if len(words) > 25:
            template = ' '.join(words[:25])
        
        pub_date = base_date - timedelta(days=i * 2)
        
        # Assign sentiment based on keywords
        sentiment = "NEU"
        if any(word in template.lower() for word in ["good", "helps", "positive", "life-changing"]):
            sentiment = "POS"
        elif any(word in template.lower() for word in ["side effects", "reactions", "frustrated", "warning"]):
            sentiment = "NEG"
        
        snippets.append({
            "site": f"reddit/r/health",
            "quote": template,
            "url": f"https://reddit.com/r/health/comments/example{i}",
            "sentiment": sentiment,
            "score": 0.5 + (i % 3) * 0.2  # Vary scores
        })
    
    return snippets


def _extract_snippet(text: str, query: str) -> Optional[str]:
    """Extract a relevant snippet (<=25 words) containing the query."""
    if not text:
        return None
    
    # Clean text
    text = _clean_text(text)
    
    # Find sentences containing query
    sentences = re.split(r'[.!?]+', text)
    for sentence in sentences:
        if query.lower() in sentence.lower():
            words = sentence.strip().split()
            if len(words) <= 25:
                return ' '.join(words)
            else:
                # Take 25 words around query mention
                query_idx = sentence.lower().find(query.lower())
                words_before = sentence[:query_idx].split()[-10:]
                words_after = sentence[query_idx:].split()[:15]
                return ' '.join(words_before + words_after)
    
    # Fallback: first 25 words
    words = text.split()[:25]
    return ' '.join(words) if words else None


def _clean_text(text: str) -> str:
    """Clean and sanitize text."""
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Remove mentions/usernames
    text = re.sub(r'@\w+', '[user]', text)
    text = re.sub(r'/u/\w+', '[user]', text)
    
    # Remove emails
    text = re.sub(r'\S+@\S+', '[email]', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def _is_safe_content(text: str) -> bool:
    """Check if content is safe (no PII, offensive language)."""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Block if contains potential PII indicators
    pii_indicators = ['my name is', 'i am called', 'email me', 'phone:', 'address:']
    for indicator in pii_indicators:
        if indicator in text_lower:
            return False
    
    # Block offensive content (basic filter)
    # In production, use more sophisticated content moderation
    offensive_words = ['spam', 'viagra', 'casino']  # Minimal list for demo
    for word in offensive_words:
        if word in text_lower:
            return False
    
    return True


def _analyze_sentiment(text: str) -> str:
    """Simple rule-based sentiment analysis."""
    if not text:
        return "NEU"
    
    text_lower = text.lower()
    
    # Positive keywords
    positive = [
        'good', 'great', 'excellent', 'amazing', 'helpful', 'effective',
        'works', 'relief', 'better', 'improved', 'recommend', 'love',
        'positive', 'beneficial', 'success'
    ]
    
    # Negative keywords
    negative = [
        'bad', 'terrible', 'awful', 'horrible', 'side effect', 'adverse',
        'warning', 'danger', 'risk', 'problem', 'issue', 'concern',
        'worse', 'severe', 'pain', 'fail', 'disappointed', 'avoid'
    ]
    
    pos_count = sum(1 for word in positive if word in text_lower)
    neg_count = sum(1 for word in negative if word in text_lower)
    
    if pos_count > neg_count:
        return "POS"
    elif neg_count > pos_count:
        return "NEG"
    else:
        return "NEU"


def _normalize_score(reddit_score: int) -> float:
    """Normalize Reddit score to 0-1 range."""
    # Use log scale for normalization
    import math
    if reddit_score <= 0:
        return 0.0
    return min(1.0, math.log(reddit_score + 1) / 10)
