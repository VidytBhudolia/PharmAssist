"""LLM-powered summarizer for web intelligence data."""

import logging
import json
from typing import Dict, List
from crewai import LLM

logger = logging.getLogger(__name__)

# Initialize LLM (same model as clinical agent)
llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=600)


def summarize(context: Dict) -> Dict:
    """
    Generate LLM-powered summary of web intelligence data.
    
    Args:
        context: Dict with:
            - query: Parsed query dict
            - signals: Signals from analytics_engine
            - news: List of news items
            - forums: List of forum snippets
            - trends: Trends data
            
    Returns:
        Dict with:
        - summary: 4-line markdown summary
        - bullets: List[str] (3 bullets, max 20 words each)
        - quotes: List[Dict] with text, source, url (max 2, <=25 words each)
        - recommended_actions: List[str] (3 actions)
        - confidence: "LOW" | "MEDIUM" | "HIGH" with reason
    """
    logger.info("Generating LLM summary")
    
    query = context.get('query', {})
    signals = context.get('signals', {})
    news = context.get('news', [])
    forums = context.get('forums', [])
    trends = context.get('trends', {})
    
    # Build prompt
    prompt = _build_prompt(query, signals, news, forums, trends)
    
    try:
        # Call LLM
        raw_response = llm.call(messages=[{"role": "user", "content": prompt}])
        
        if not isinstance(raw_response, str):
            raw_response = str(raw_response)
        
        # Parse JSON response
        result = _parse_llm_response(raw_response, news, forums)
        
        logger.info(f"Summary generated with confidence: {result['confidence']}")
        return result
        
    except Exception as e:
        logger.error(f"LLM summarization failed: {e}")
        # Fallback to template-based summary
        return _fallback_summary(query, signals, news, forums)


def _build_prompt(
    query: Dict,
    signals: Dict,
    news: List[Dict],
    forums: List[Dict],
    trends: Dict
) -> str:
    """Build the LLM prompt with strict instructions."""
    
    drug = query.get('drug', 'N/A')
    disease = query.get('disease', 'N/A')
    region = query.get('region', 'Global')
    timespan = query.get('timespan_days', 90)
    
    signal_score = signals.get('signalScore', 0)
    trend_delta = signals.get('trend_delta_pct', 0)
    news_volume = signals.get('news_volume', 0)
    sentiment = signals.get('sentiment', {})
    why_list = signals.get('why', [])
    
    # Format news items
    news_str = ""
    for i, item in enumerate(news[:10], 1):
        news_str += f"{i}. {item['title']}\n"
        news_str += f"   Source: {item['source']}\n"
        news_str += f"   URL: {item['url']}\n"
        news_str += f"   Snippet: {item['snippet'][:150]}...\n"
        news_str += f"   Tags: {', '.join(item.get('tags', []))}\n\n"
    
    # Format forum items
    forum_str = ""
    for i, item in enumerate(forums[:15], 1):
        forum_str += f"{i}. \"{item['quote']}\" (Sentiment: {item['sentiment']})\n"
        forum_str += f"   Source: {item['site']}\n"
        forum_str += f"   URL: {item['url']}\n\n"
    
    # Build prompt
    prompt = f"""You are a concise pharmaceutical research assistant analyzing web intelligence signals.

TASK: Provide a structured analysis of the following data.

QUERY CONTEXT:
- Drug: {drug}
- Disease/Condition: {disease}
- Region: {region}
- Timespan: Last {timespan} days

COMPUTED SIGNALS:
- Signal Score: {signal_score} / 100
- Search Trend Change: {trend_delta:+.1f}% (30-day)
- News Volume: {news_volume} articles
- Patient Sentiment: {sentiment.get('positive', 0)} positive, {sentiment.get('neutral', 0)} neutral, {sentiment.get('negative', 0)} negative
- Key Factors: {', '.join(why_list)}

TOP NEWS ARTICLES (with URLs):
{news_str if news_str else "No news articles available."}

PATIENT FORUM QUOTES (with URLs):
{forum_str if forum_str else "No forum data available."}

STRICT OUTPUT REQUIREMENTS:

1. TOP SIGNAL (1 line):
   - State the signalScore / 100 and a brief interpretation

2. TL;DR (3 concise bullets, max 20 words each):
   - Summarize key findings
   - Be specific and data-driven

3. WHAT CHANGED (1 sentence):
   - Explain the primary change or trend

4. EVIDENCE QUOTES (exactly 2 quotes, each <=25 words):
   - Extract SHORT quotes from the news or forum data provided above
   - CRITICAL: Only use text that appears in the data above
   - MUST include the exact source URL from the provided data
   - Format: {{"text": "quote text", "source": "source name", "url": "exact URL from data"}}

5. RECOMMENDED ACTIONS (exactly 3 short, actionable items):
   - Keep each action concise (10-15 words)
   - Be practical and relevant

6. CONFIDENCE (1 line):
   - State: HIGH, MEDIUM, or LOW
   - Brief reason (data quality, volume, etc.)

CRITICAL RULES:
- DO NOT invent or hallucinate source URLs
- Only cite URLs that are explicitly provided in the data above
- If no good quotes are available, use generic summaries with [No direct quote available]
- Keep all text concise and factual
- Include the disclaimer at the end

Return your response as a valid JSON object with these exact keys:
{{
  "top_signal": "...",
  "bullets": ["...", "...", "..."],
  "what_changed": "...",
  "quotes": [
    {{"text": "...", "source": "...", "url": "..."}},
    {{"text": "...", "source": "...", "url": "..."}}
  ],
  "recommended_actions": ["...", "...", "..."],
  "confidence": "HIGH/MEDIUM/LOW",
  "confidence_reason": "..."
}}
"""
    
    return prompt


def _parse_llm_response(raw: str, news: List[Dict], forums: List[Dict]) -> Dict:
    """Parse LLM JSON response."""
    # Find JSON in response
    start = raw.find('{')
    end = raw.rfind('}')
    
    if start == -1 or end == -1:
        raise ValueError("No JSON found in LLM response")
    
    json_str = raw[start:end+1]
    data = json.loads(json_str)
    
    # Validate quotes URLs (safety check)
    quotes = data.get('quotes', [])
    validated_quotes = []
    
    valid_urls = set(item['url'] for item in news) | set(item['url'] for item in forums)
    
    for quote in quotes[:2]:  # Max 2 quotes
        if quote.get('url') in valid_urls or '[No direct quote available]' in quote.get('text', ''):
            # Ensure quote is <=25 words
            text = quote.get('text', '')
            words = text.split()
            if len(words) > 25:
                text = ' '.join(words[:25])
            
            validated_quotes.append({
                "text": text,
                "source": quote.get('source', 'Unknown'),
                "url": quote.get('url', '')
            })
    
    # Build final summary markdown
    summary_md = f"{data.get('top_signal', '')}\n\n"
    summary_md += "**TL;DR:**\n"
    for bullet in data.get('bullets', [])[:3]:
        summary_md += f"- {bullet}\n"
    summary_md += f"\n**What Changed:** {data.get('what_changed', '')}\n"
    
    # Add disclaimer
    disclaimer = "\n*This is an informational signal. Not medical or legal advice.*"
    
    return {
        "summary": summary_md + disclaimer,
        "bullets": data.get('bullets', [])[:3],
        "quotes": validated_quotes,
        "recommended_actions": data.get('recommended_actions', [])[:3],
        "confidence": data.get('confidence', 'MEDIUM'),
        "confidence_reason": data.get('confidence_reason', 'Standard analysis')
    }


def _fallback_summary(
    query: Dict,
    signals: Dict,
    news: List[Dict],
    forums: List[Dict]
) -> Dict:
    """Generate fallback summary if LLM fails."""
    logger.warning("Using fallback summary")
    
    drug = query.get('drug', 'the drug')
    signal_score = signals.get('signalScore', 0)
    why_list = signals.get('why', [])
    
    summary_md = f"**Signal Score: {signal_score}/100**\n\n"
    summary_md += "**TL;DR:**\n"
    summary_md += f"- Web signals detected for {drug}\n"
    summary_md += f"- {signals.get('news_volume', 0)} news articles found\n"
    summary_md += f"- Search trend change: {signals.get('trend_delta_pct', 0):+.1f}%\n"
    summary_md += f"\n**What Changed:** {why_list[0] if why_list else 'Baseline monitoring'}\n"
    summary_md += "\n*This is an informational signal. Not medical or legal advice.*"
    
    return {
        "summary": summary_md,
        "bullets": [
            f"Web signals detected for {drug}",
            f"{signals.get('news_volume', 0)} news articles analyzed",
            f"Search trend: {signals.get('trend_delta_pct', 0):+.1f}%"
        ],
        "quotes": [],
        "recommended_actions": [
            "Monitor ongoing developments",
            "Review detailed news articles",
            "Track patient forum discussions"
        ],
        "confidence": "LOW",
        "confidence_reason": "LLM summarization unavailable"
    }
