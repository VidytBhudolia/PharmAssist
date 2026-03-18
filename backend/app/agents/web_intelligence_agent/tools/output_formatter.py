"""Output formatter for UI-ready JSON with visualizations."""

import logging
from datetime import datetime
from typing import Dict, List, Any
from app.models.visualization import Visualization, VisualizationType, VizConfig
from app.services.agent_scorer import score_web_intelligence
from .analytics_engine import compute_alert_level

logger = logging.getLogger(__name__)


def format_ui(
    summary_dict: Dict,
    signals: Dict,
    trends: Dict,
    news: List[Dict],
    forums: List[Dict],
    query: Dict
) -> Dict:
    """
    Format final UI JSON with visualizations.
    
    Args:
        summary_dict: Summary from llm_summarizer
        signals: Signals from analytics_engine
        trends: Trends data
        news: Cleaned news items
        forums: Cleaned forum items
        query: Original parsed query
        
    Returns:
        UI JSON dict with:
        - header: Query metadata
        - top_signal: Signal score and interpretation
        - trend_sparkline: Visualization data
        - top_headlines: News list
        - forum_quotes: Forum list
        - sentiment: Sentiment breakdown
        - recommended_actions: Action items
        - confidence: Analysis confidence
        - lastUpdated: ISO timestamp
        - visualizations: List of Visualization objects
    """
    logger.info("Formatting UI output")
    
    signal_score = signals.get('signalScore', 0)
    alert_level = compute_alert_level(signal_score)
    
    # Build header
    header = {
        "drug": query.get('drug', 'N/A'),
        "disease": query.get('disease', 'N/A'),
        "region": query.get('region', 'Global'),
        "timespan_days": query.get('timespan_days', 90),
        "granularity": query.get('granularity', 'daily')
    }
    
    # Top signal
    top_signal = {
        "score": signal_score,
        "label": alert_level,
        "text": summary_dict.get('summary', ''),
        "why": signals.get('why', [])
    }
    
    # Trend sparkline visualization
    trend_sparkline = _build_sparkline_viz(trends, query.get('drug', 'Drug'))
    
    # Sentiment visualization
    sentiment_viz = _build_sentiment_viz(signals.get('sentiment', {}))
    
    # News tags visualization
    tags_viz = _build_tags_viz(signals.get('news_tags_counts', {}))
    
    # Format headlines
    formatted_headlines = []
    for item in news[:10]:
        formatted_headlines.append({
            "title": item.get('title', ''),
            "url": item.get('url', ''),
            "source": item.get('source', ''),
            "publishedAt": item.get('publishedAt', ''),
            "snippet": item.get('snippet', ''),
            "tags": item.get('tags', [])
        })
    
    # Format forum quotes
    formatted_quotes = []
    for item in forums[:15]:
        formatted_quotes.append({
            "quote": item.get('quote', ''),
            "site": item.get('site', ''),
            "url": item.get('url', ''),
            "sentiment": item.get('sentiment', 'NEU'),
            "score": item.get('score', 0)
        })
    
    # Sentiment summary - PERCENTAGES ONLY (no absolute counts)
    sentiment_data = signals.get('sentiment', {})
    total_sentiment = (
        sentiment_data.get('positive', 0) + 
        sentiment_data.get('neutral', 0) + 
        sentiment_data.get('negative', 0)
    )
    
    # Calculate percentages (avoid division by zero)
    if total_sentiment > 0:
        sentiment_summary = {
            "positive": round((sentiment_data.get('positive', 0) / total_sentiment) * 100, 1),
            "neutral": round((sentiment_data.get('neutral', 0) / total_sentiment) * 100, 1),
            "negative": round((sentiment_data.get('negative', 0) / total_sentiment) * 100, 1)
        }
    else:
        sentiment_summary = {
            "positive": 0,
            "neutral": 0,
            "negative": 0
        }
    
    # Build canonical summary object for banner
    news_count = len(formatted_headlines)
    forum_count = len(formatted_quotes)
    positive_pct = sentiment_summary.get("positive", 0)
    negative_pct = sentiment_summary.get("negative", 0)
    
    has_data = news_count > 0 or forum_count > 0
    
    # Determine answer based on sentiment and signal score
    if not has_data:
        banner_answer = "No data"
    elif negative_pct > 40:
        banner_answer = "Caution"
    elif positive_pct > 50:
        banner_answer = "Positive"
    else:
        banner_answer = "Mixed"
    
    banner_summary = {
        "researcherQuestion": "Is the market sentiment favorable?",
        "answer": banner_answer,
        "explainers": []
    }
    
    if news_count > 0:
        banner_summary["explainers"].append(f"{news_count} news articles found")
    if positive_pct > 0 or negative_pct > 0:
        banner_summary["explainers"].append(f"Sentiment: {positive_pct:.0f}% positive, {negative_pct:.0f}% negative")
    if alert_level and alert_level != "LOW":
        banner_summary["explainers"].append(f"Alert level: {alert_level}")

    # ── Feasibility score ──
    _signal = top_signal.get("score") if top_signal else None
    _web_score = score_web_intelligence(
        positive_pct=positive_pct,
        negative_pct=negative_pct,
        neutral_pct=sentiment_summary.get("neutral", 0),
        news_count=news_count,
        forum_count=forum_count,
        signal_score=_signal,
        has_critical_alert=(alert_level == "CRITICAL") if alert_level else False,
    )
    banner_summary["feasibilityScore"] = _web_score
    logger.info(f"Web Intelligence feasibility score: {_web_score['score']}/100 ({_web_score['label']})")

    # Generate suggested next prompts
    drug_name = header.get("drug", "drug")
    disease_name = header.get("disease", "disease")
    suggested_next_prompts = [
        {"prompt": f"Show clinical trials for {drug_name}"},
        {"prompt": f"Analyze patent risk for {drug_name} in {disease_name}"},
        {"prompt": f"Get market size data for {drug_name}"}
    ]
    
    # Build final output - Match frontend expected field names
    output = {
        "header": header,
        "summary": banner_summary,  # Canonical summary for UI banner
        "top_signal": top_signal,  # Signal summary with score and interpretation
        "trend_sparkline": trend_sparkline.dict() if trend_sparkline else None,
        "top_headlines": formatted_headlines,  # Keep for backward compatibility
        "news_articles": formatted_headlines,  # Frontend expects this field name
        "news": formatted_headlines,  # Also alias
        "forum_quotes": formatted_quotes,
        "forums": formatted_quotes,  # Alias for frontend
        "sentiment": sentiment_summary,  # Keep for backward compatibility
        "sentiment_summary": sentiment_summary,  # Frontend expects this field name
        "sentiment_viz": sentiment_viz.dict() if sentiment_viz else None,
        "tags_viz": tags_viz.dict() if tags_viz else None,
        "quotes": summary_dict.get('quotes', []),
        "recommended_actions": summary_dict.get('recommended_actions', []),
        "recommendations": summary_dict.get('recommended_actions', []),  # Alias
        "confidence": summary_dict.get('confidence', 'MEDIUM'),  # Add confidence field
        "lastUpdated": datetime.now().isoformat(),
        "suggestedNextPrompts": suggested_next_prompts,
        "visualizations": [
            trend_sparkline.dict() if trend_sparkline else None,
            sentiment_viz.dict() if sentiment_viz else None,
            tags_viz.dict() if tags_viz else None
        ]
    }
    
    # Filter out None visualizations
    output['visualizations'] = [v for v in output['visualizations'] if v is not None]
    
    logger.info("UI output formatted successfully")
    return output


def _build_sparkline_viz(trends: Dict, drug_name: str) -> Visualization:
    """Build sparkline visualization for trends."""
    timeseries = trends.get('timeseries', [])
    
    if not timeseries:
        return None
    
    # Format data for line chart
    data = [
        {"date": point['date'], "value": point['value']}
        for point in timeseries
    ]
    
    return Visualization(
        id="web_intel_trends",
        vizType=VisualizationType.LINE,
        title=f"Search Interest Trend - {drug_name}",
        description=f"30-day change: {trends.get('pct_change_30d', 0):+.1f}%",
        data=data,
        config=VizConfig(
            xField="date",
            yField="value",
            orientation="horizontal",
            legend=False,
            tooltip=True,
            colors=["#3b82f6"]
        ),
        source="Google Trends",
        meta={
            "pct_change_30d": trends.get('pct_change_30d', 0),
            "related_queries": trends.get('top_related', []),
            "breakout_terms": trends.get('breakout_terms', [])
        }
    )


def _build_sentiment_viz(sentiment: Dict) -> Visualization:
    """Build donut/pie chart for sentiment distribution - PERCENTAGES ONLY."""
    positive = sentiment.get('positive', 0)
    neutral = sentiment.get('neutral', 0)
    negative = sentiment.get('negative', 0)
    
    total = positive + neutral + negative
    
    if total == 0:
        return None
    
    # Calculate percentages for display
    pos_pct = round((positive / total) * 100, 1)
    neu_pct = round((neutral / total) * 100, 1)
    neg_pct = round((negative / total) * 100, 1)
    
    # Use percentages as values for visualization
    data = [
        {"label": "Positive", "value": pos_pct},
        {"label": "Neutral", "value": neu_pct},
        {"label": "Negative", "value": neg_pct}
    ]
    
    return Visualization(
        id="web_intel_sentiment",
        vizType=VisualizationType.PIE,
        title="Patient Sentiment",
        description="Distribution of sentiment in forum discussions",
        data=data,
        config=VizConfig(
            labelField="label",
            valueField="value",
            legend=True,
            tooltip=True,
            colors=["#10b981", "#6b7280", "#ef4444"]  # Green, gray, red
        ),
        source="Patient Forums"
    )


def _build_tags_viz(tags: Dict[str, int]) -> Visualization:
    """Build bar chart for news tags distribution."""
    if not tags:
        return None
    
    # Sort by count
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    
    # Take top 8
    data = [
        {"tag": tag, "count": count}
        for tag, count in sorted_tags[:8]
    ]
    
    if not data:
        return None
    
    return Visualization(
        id="web_intel_tags",
        vizType=VisualizationType.BAR,
        title="News Topics",
        description="Most frequent tags in news coverage",
        data=data,
        config=VizConfig(
            xField="tag",
            yField="count",
            orientation="vertical",
            legend=False,
            tooltip=True,
            colors=["#8b5cf6"]
        ),
        source="News Analysis",
        meta={"total_tags": len(tags)}
    )


def render_sparkline(name: str, series: List[Dict]) -> Visualization:
    """
    Helper to render a sparkline chart.
    
    Args:
        name: Chart name
        series: List of {"date": str, "value": float} dicts
        
    Returns:
        Visualization object
    """
    return Visualization(
        id=f"sparkline_{name.lower().replace(' ', '_')}",
        vizType=VisualizationType.LINE,
        title=name,
        data=series,
        config=VizConfig(
            xField="date",
            yField="value",
            legend=False,
            tooltip=True
        )
    )


def render_headline_list(items: List[Dict]) -> List[Dict]:
    """
    Format headlines for display.
    
    Args:
        items: List of news item dicts
        
    Returns:
        Formatted list for UI
    """
    return [
        {
            "title": item.get('title', ''),
            "url": item.get('url', ''),
            "source": item.get('source', ''),
            "date": item.get('publishedAt', ''),
            "snippet": item.get('snippet', '')[:200]
        }
        for item in items
    ]
