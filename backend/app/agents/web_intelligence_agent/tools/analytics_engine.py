"""Analytics engine for computing web intelligence signals."""

import logging
from typing import Dict, List
from collections import Counter

logger = logging.getLogger(__name__)

# Default scoring weights (can be overridden via config)
DEFAULT_WEIGHTS = {
    "trend": 0.5,
    "news": 0.3,
    "sentiment": 0.2
}


def compute_signals(
    trends: Dict,
    news: List[Dict],
    forums: List[Dict],
    weights: Dict = None
) -> Dict:
    """
    Compute web intelligence signals from raw data.
    
    Args:
        trends: Trends data dict from trends_fetcher
        news: List of news items
        forums: List of forum snippets
        weights: Optional scoring weights dict
        
    Returns:
        Dict with:
        - signalScore: int (0-100)
        - trend_delta_pct: float
        - news_volume: int
        - news_tags_counts: Dict[str, int]
        - sentiment: Dict with positive/neutral/negative counts and neg_pct
        - top_headlines: List[Dict] (top 5 news items)
        - why: List[str] (reasons for signal score)
    """
    logger.info("Computing analytics signals")
    
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    # Trend component
    trend_delta_pct = trends.get('pct_change_30d', 0.0)
    trend_component = _compute_trend_component(trend_delta_pct)
    
    # News component
    news_volume = len(news)
    news_component = _compute_news_component(news_volume)
    
    # News tags analysis
    news_tags_counts = _count_news_tags(news)
    
    # Sentiment component
    sentiment = _compute_sentiment(forums)
    sentiment_component = sentiment['neg_pct']
    
    # Weighted signal score (0-100)
    signal_score = int(
        weights['trend'] * trend_component +
        weights['news'] * news_component +
        weights['sentiment'] * sentiment_component
    )
    signal_score = max(0, min(100, signal_score))  # Clamp to 0-100
    
    # Generate explanation
    why = _generate_why(trend_delta_pct, news_volume, news_tags_counts, sentiment)
    
    # Top headlines
    top_headlines = news[:5] if news else []
    
    result = {
        "signalScore": signal_score,
        "trend_delta_pct": round(trend_delta_pct, 2),
        "news_volume": news_volume,
        "news_tags_counts": news_tags_counts,
        "sentiment": sentiment,
        "top_headlines": top_headlines,
        "why": why
    }
    
    logger.info(f"Signal score: {signal_score}/100")
    return result


def _compute_trend_component(pct_change: float) -> float:
    """
    Compute trend component score (0-100).
    
    Higher absolute change = higher score
    """
    # Normalize: abs change of 50% = score of 100
    score = min(abs(pct_change) * 2, 100)
    return score


def _compute_news_component(news_volume: int) -> float:
    """
    Compute news component score (0-100).
    
    More news = higher signal
    """
    # Normalize: 10+ news items = max score
    score = min((news_volume / 10) * 100, 100)
    return score


def _compute_sentiment(forums: List[Dict]) -> Dict:
    """
    Compute sentiment statistics.
    
    Returns:
        Dict with positive, neutral, negative counts and neg_pct
    """
    if not forums:
        return {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "neg_pct": 0.0
        }
    
    sentiment_counts = Counter(item.get('sentiment', 'NEU') for item in forums)
    
    positive = sentiment_counts.get('POS', 0)
    neutral = sentiment_counts.get('NEU', 0)
    negative = sentiment_counts.get('NEG', 0)
    total = positive + neutral + negative
    
    neg_pct = (negative / total * 100) if total > 0 else 0.0
    
    return {
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "neg_pct": round(neg_pct, 2)
    }


def _count_news_tags(news: List[Dict]) -> Dict[str, int]:
    """Count frequency of news tags."""
    all_tags = []
    for item in news:
        tags = item.get('tags', [])
        all_tags.extend(tags)
    
    tag_counts = Counter(all_tags)
    return dict(tag_counts)


def _generate_why(
    trend_delta: float,
    news_volume: int,
    tags: Dict[str, int],
    sentiment: Dict
) -> List[str]:
    """
    Generate human-readable explanations for the signal score.
    
    Returns list of reason strings
    """
    reasons = []
    
    # Trend reasons
    if abs(trend_delta) > 20:
        direction = "increase" if trend_delta > 0 else "decrease"
        reasons.append(f"Significant search trend {direction} ({trend_delta:+.1f}%)")
    elif abs(trend_delta) > 5:
        direction = "increase" if trend_delta > 0 else "decrease"
        reasons.append(f"Moderate search trend {direction} ({trend_delta:+.1f}%)")
    
    # News reasons
    if news_volume >= 10:
        reasons.append(f"High news volume ({news_volume} articles)")
    elif news_volume >= 5:
        reasons.append(f"Notable news coverage ({news_volume} articles)")
    
    # Tag-based reasons
    critical_tags = ['supply', 'safety', 'recall', 'outbreak']
    for tag in critical_tags:
        count = tags.get(tag, 0)
        if count > 0:
            reasons.append(f"News reports: {tag} issues ({count} mentions)")
    
    # Sentiment reasons
    neg_pct = sentiment.get('neg_pct', 0)
    if neg_pct > 40:
        reasons.append(f"High negative sentiment in patient forums ({neg_pct:.0f}%)")
    elif neg_pct > 25:
        reasons.append(f"Elevated negative sentiment ({neg_pct:.0f}%)")
    
    if not reasons:
        reasons.append("Stable baseline signals")
    
    return reasons


def compute_alert_level(signal_score: int) -> str:
    """
    Compute alert level from signal score.
    
    Returns:
        "HIGH" | "MEDIUM" | "LOW"
    """
    if signal_score >= 70:
        return "HIGH"
    elif signal_score >= 40:
        return "MEDIUM"
    else:
        return "LOW"
