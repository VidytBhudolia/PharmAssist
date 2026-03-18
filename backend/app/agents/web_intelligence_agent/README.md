# Web Intelligence Agent

## Overview

The Web Intelligence Agent gathers real-time public web signals about drugs and diseases from search trends, news, and patient forums. It returns LLM-curated summaries with hyperlinked evidence and visual widgets (sparklines, sentiment charts).

**Key Features:**
- Google Trends search interest analysis
- News aggregation from health sources (WHO, CDC, FDA RSS feeds)
- Patient forum sentiment analysis (Reddit)
- LLM-powered summarization with strict source citation
- Visual widgets (trend sparklines, sentiment donut charts, news tag distributions)
- Caching layer with TTL for performance

**Important:** This agent does NOT handle patent data. For patent information, use the `patent_agent`.

---

## Architecture

Follows the `clinical_agent` pattern:

1. **Input Parsing** → Parse free-text query, resolve synonyms, normalize regions
2. **Tool Orchestration** → Execute tools in sequence (trends → news → forums → preprocessing → analytics)
3. **LLM Summarization** → Generate curated summary with citations
4. **Output Formatting** → Return UI-ready JSON with visualizations

---

## Installation

### Dependencies

Add to `requirements.txt`:

```
pytrends>=4.9.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
praw>=7.7.0  # Optional, for Reddit API
```

Install:

```bash
pip install -r requirements.txt
```

### Data Files

Required data files (already included):
- `data/drug_synonyms.json` - Drug name synonyms
- `data/disease_synonyms.json` - Disease name synonyms

### Environment Variables (Optional)

For enhanced query parsing and summarization:
```bash
# Set Groq API key for LLM features
export GROQ_API_KEY="your_groq_api_key_here"

# Reddit API (optional, for real forum data)
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_secret"
export REDDIT_USER_AGENT="your_app_name"
```

**Note:** The agent works WITHOUT API keys using:
- Regex-based query parsing (fallback from LLM)
- Stub data for Google Trends (on rate limits)
- Fallback summaries (if LLM unavailable)

---

## Testing

### Quick Test (No API Keys Required)

From workspace root:
```bash
cd e:\workspace\pharmassist
python test_web_intel.py
```

Expected output:
```
Test 1: What are the web signals for hypertension?
Status: success
Disease: hypertension
Signal Score: 38/100

Test 2: Show me trends for metformin in India over last 30 days
Status: success
Drug: metformin
Signal Score: 19/100

Test 3: Aspirin trends worldwide
Status: success
Drug: aspirin
Signal Score: 22/100
```

### Unit Tests (20 Tests)

```bash
cd e:\workspace\pharmassist\backend
python -m pytest tests/agents/web_intelligence/test_agent.py -v
```

Expected: **20 passed** in ~19 seconds

### Manual Testing (Python REPL)

```bash
cd e:\workspace\pharmassist\backend
python
```

```python
from app.agents.web_intelligence_agent.web_intelligence_agent import run

# Test with query
result = run("What are the web signals for diabetes in the US?")
print(f"Status: {result['status']}")

# Check structure
if result['status'] == 'success':
    data = result['data']
    print(f"Disease: {data['header']['disease']}")
    print(f"Signal Score: {data['top_signal']['score']}/100")
    print(f"Headlines: {len(data['top_headlines'])}")
```

### Test Individual Tools

```python
from app.agents.web_intelligence_agent.tools import trends_fetcher, news_fetcher

# Test trends
trends = trends_fetcher.get_trends("aspirin", "US", 30, "daily")
print(f"Data points: {len(trends['timeseries'])}")
print(f"30d change: {trends['pct_change_30d']}%")

# Test news
news = news_fetcher.get_news("diabetes treatment", max_articles=5)
print(f"Articles: {len(news['articles'])}")
```

### Verify pytrends Installation

```python
from app.agents.web_intelligence_agent.tools.trends_fetcher import PYTRENDS_AVAILABLE
print(f"Real Google Trends available: {PYTRENDS_AVAILABLE}")  # Should be True
```

---

## Usage

### Basic Usage

```python
from app.agents.web_intelligence_agent import run

result = run("Show me web signals for metformin for diabetes in India over the last 90 days")

if result['status'] == 'success':
    data = result['data']
    print(f"Signal Score: {data['top_signal']['score']}/100")
    print(f"Confidence: {data['confidence']}")
    print(f"Headlines: {len(data['top_headlines'])}")
```

### Sample Inputs

```python
# Drug + disease + region + timespan
run("Show me web signals for metformin for diabetes in India over the last 90 days")

# Drug only, global, default timespan
run("Monitor ibuprofen worldwide last 30 days, highlight news & patient sentiment")

# Disease focus
run("What are the web signals for hypertension in the last 60 days?")

# Short form
run("aspirin trends")
```

---

## API Reference

### Main Function

```python
def run(request_text: str) -> Dict:
    """
    Main entrypoint for Web Intelligence Agent.
    
    Args:
        request_text: Free-text user query
        
    Returns:
        Dict with:
        - status: "success" | "error"
        - data: UI JSON (if success) - see Output Schema below
        - message: Error message (if error)
    """
```

### Output Schema

```json
{
  "status": "success",
  "data": {
    "header": {
      "drug": "metformin",
      "disease": "diabetes",
      "region": "IN",
      "timespan_days": 90,
      "granularity": "daily"
    },
    "top_signal": {
      "score": 65,                    // 0-100
      "label": "MEDIUM",              // HIGH | MEDIUM | LOW
      "text": "Markdown summary...",
      "why": ["reason1", "reason2"]
    },
    "trend_sparkline": { ... },       // Visualization object
    "top_headlines": [
      {
        "title": "...",
        "url": "...",
        "source": "...",
        "publishedAt": "ISO datetime",
        "snippet": "...",
        "tags": ["safety", "supply"]
      }
    ],
    "forum_quotes": [
      {
        "quote": "...",
        "site": "reddit/r/diabetes",
        "url": "...",
        "sentiment": "POS",            // POS | NEU | NEG
        "score": 0.8
      }
    ],
    "sentiment": {
      "positive": 10,
      "neutral": 5,
      "negative": 3,
      "neg_pct": 16.67,
      "total": 18
    },
    "sentiment_viz": { ... },          // Visualization object
    "tags_viz": { ... },               // Visualization object
    "quotes": [
      {
        "text": "Short quote ≤25 words",
        "source": "Source Name",
        "url": "https://..."
      }
    ],
    "recommended_actions": [
      "Action 1",
      "Action 2",
      "Action 3"
    ],
    "confidence": "HIGH",              // HIGH | MEDIUM | LOW
    "confidence_reason": "...",
    "lastUpdated": "ISO datetime",
    "visualizations": [ ... ]          // Array of Visualization objects
  }
}
```

---

## Tools

### 1. `trends_fetcher.py`

Fetches search interest trends from Google Trends (with fallback stub).

```python
get_trends(keyword, region, timespan_days, granularity) -> Dict
```

**Returns:** Timeseries data (0-100 normalized), 30-day % change, related queries, breakout terms.

**Caching:** 1 hour TTL

---

### 2. `news_fetcher.py`

Fetches news from RSS feeds (WHO, CDC, FDA) and web search fallback.

```python
get_news(query, region, since_days, max_items) -> List[Dict]
```

**Returns:** List of articles with title, URL, source, date, snippet, tags.

**Tags:** `supply`, `safety`, `guideline`, `policy`, `approval`, `recall`, `outbreak`, `research`

**Caching:** 30 minutes TTL

---

### 3. `forum_fetcher.py`

Fetches anonymized patient forum quotes (Reddit, with stub fallback).

```python
get_forum_snippets(query, subreddit_list, since_days, max_items) -> List[Dict]
```

**Returns:** List of quotes (≤25 words), sentiment (POS/NEU/NEG), site, URL.

**Safety:** Removes PII, sanitizes usernames, filters offensive content.

**Caching:** 1 hour TTL

---

### 4. `preprocessor.py`

Cleans text, removes HTML/boilerplate, deduplicates items.

```python
clean_items(news_items, forum_items) -> Dict
```

**Returns:** Cleaned and deduplicated news and forums.

---

### 5. `analytics_engine.py`

Computes web intelligence signals from raw data.

```python
compute_signals(trends, news, forums, weights) -> Dict
```

**Returns:** Signal score (0-100), trend delta, news volume, sentiment stats, tags counts, top headlines, explanations.

**Scoring Formula:**
```
signalScore = 0.5 * trend_component + 0.3 * news_component + 0.2 * sentiment_component
```

---

### 6. `llm_summarizer.py`

Generates LLM-powered summary with strict citation rules.

```python
summarize(context) -> Dict
```

**Returns:** Summary markdown, bullets, quotes (with URLs), recommended actions, confidence.

**LLM Rules:**
- Never invent or hallucinate source URLs
- Only cite URLs from provided data
- Quotes ≤25 words
- Include disclaimer: "This is an informational signal. Not medical or legal advice."

---

### 7. `output_formatter.py`

Formats data for UI with visualizations.

```python
format_ui(summary_dict, signals, trends, news, forums, query) -> Dict
```

**Returns:** Complete UI JSON with embedded Visualization objects.

**Visualizations:**
- Trend sparkline (line chart)
- Sentiment donut chart (pie)
- News tags bar chart

---

### 8. `cache_layer.py`

In-memory TTL cache with optional Redis fallback.

```python
get(key) -> Optional[Any]
set(key, value, ttl_seconds)
clear(key)
```

**Default TTL:** 10-60 minutes depending on data type.

---

## Testing

Run unit tests:

```bash
cd backend
pytest tests/agents/web_intelligence/test_agent.py -v
```

### Test Coverage

- Input parsing and synonym resolution
- Cache set/get/expiry
- Trends data structure and normalization
- News fetching and deduplication
- Forum quotes (word limit, sentiment)
- Preprocessor cleaning and deduplication
- Analytics signal computation (0-100 range)
- Full integration test (end-to-end)

---

## Example Run

See `examples/run_web_intel.py`:

```bash
cd backend
python -m examples.run_web_intel
```

**Output:**
```
=== Web Intelligence Agent Demo ===

Query: Show me web signals for metformin for diabetes in India over the last 90 days

Status: success

Signal Score: 58/100 (MEDIUM)

Confidence: HIGH - Strong data coverage from multiple sources

Top Headlines (5):
1. New Study Reveals Benefits of metformin for Long-term Treatment
2. metformin Supply Chain Issues Reported in Multiple Regions
...

Patient Sentiment:
- Positive: 8
- Neutral: 5
- Negative: 2
- Negative %: 13.33%

Recommended Actions:
1. Monitor ongoing developments
2. Review detailed news articles
3. Track patient forum discussions
```

---

## Configuration

### Rate Limits

Default rate limits (configured in tools):
- Google Trends: 1 request/sec
- News RSS: No limit (public feeds)
- Reddit: Per Reddit API TOS (if using PRAW)

### Scoring Weights

Adjust in `analytics_engine.py`:

```python
DEFAULT_WEIGHTS = {
    "trend": 0.5,    # Search trend component
    "news": 0.3,     # News volume component
    "sentiment": 0.2  # Forum sentiment component
}
```

### LLM Model

Change in `llm_summarizer.py`:

```python
llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=600)
```

---

## Validation Checklist

**Step 0:** Repository structure
- ✅ Directory `agents/web_intelligence_agent/tools/` created
- ✅ All tool files present with docstrings
- ✅ Imports pass: `python -c "import app.agents.web_intelligence_agent"`

**Step 1:** Input parser
- ✅ Unit tests pass for parsing
- ✅ Synonyms resolved correctly
- ✅ Region normalized to ISO-2

**Step 2:** Trends fetcher
- ✅ Returns timeseries with 10+ entries for 90-day query
- ✅ Values normalized 0-100
- ✅ Caching works (second call hits cache)

**Step 3:** News fetcher
- ✅ Returns deduplicated max_items with required fields
- ✅ Tags applied correctly

**Step 4:** Forum fetcher
- ✅ Returns ≤max_items
- ✅ Quotes ≤25 words
- ✅ Sentiment computed

**Step 5:** Preprocess + Analytics
- ✅ Signal score in 0-100 range
- ✅ Sentiment counts sum correctly

**Step 6:** LLM summarizer
- ✅ Output has all required keys
- ✅ Quotes only reference provided URLs

**Step 7:** Output formatter
- ✅ Sparkline data matches trends
- ✅ Donut labels non-null (no NaN)
- ✅ Score 0-100 present in top_signal

**Step 8:** Integration test
- ✅ Full flow returns success
- ✅ lastUpdated present
- ✅ top_headlines length > 0
- ✅ recommended_actions length == 3
- ✅ confidence in [LOW, MEDIUM, HIGH]

---

## Troubleshooting

### Issue: "No trends data available"

**Solution:** pytrends may be rate-limited. The agent automatically falls back to stub data. Wait 60 seconds and retry, or check your IP is not blocked by Google.

### Issue: "News fetch timeout"

**Solution:** RSS feeds may be slow. Increase timeout in `news_fetcher.py`:

```python
response = requests.get(source['rss'], headers=headers, timeout=20)  # Increase from 10
```

### Issue: "LLM summarization failed"

**Solution:** Check LLM API credentials. Agent uses fallback template-based summary if LLM fails.

### Issue: "Import error for pytrends"

**Solution:** Install dependencies:

```bash
pip install pytrends beautifulsoup4 lxml
```

---

## Future Enhancements

1. **NewsAPI Integration:** Add paid NewsAPI for better news coverage
2. **Multiple Languages:** Support non-English regions
3. **Alert System:** Webhook notifications when signal score > threshold
4. **Historical Tracking:** Store signals over time for trend analysis
5. **More Forums:** Add support for other patient forums (HealthUnlocked, Inspire)
6. **Sentiment Model:** Replace rule-based sentiment with ML model
7. **Redis Caching:** Enable distributed caching for production

---

## Contact & Support

For issues or questions, contact the PharmAssist development team.

**Documentation Version:** 1.0  
**Last Updated:** January 29, 2026
