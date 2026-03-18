"""Web Intelligence Agent for real-time public web signals."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Dict, Optional, Tuple

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from crewai import LLM

from .utils.region_normalizer import normalize_region
from .tools import (
    trends_fetcher,
    news_fetcher,
    forum_fetcher,
    preprocessor,
    analytics_engine,
    llm_summarizer,
    output_formatter
)

logger = logging.getLogger(__name__)

# Initialize LLM (same as clinical_agent)
llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=400)


def _parse_user_input(text: str) -> Dict:
    """
    Parse user prompt into canonical query structure.
    
    Resolves drug/disease synonyms and normalizes regions.
    
    Args:
        text: Free-text user query
        
    Returns:
        Canonical dict with:
        - drug: str or None
        - disease: str or None
        - region: str (ISO-2 or "GLOBAL")
        - timespan_days: int
        - granularity: "daily" or "weekly"
        - max_news: int
        - include_forums: bool
    """
    logger.info(f"Parsing user input: {text}")
    
    # Use LLM to extract structured fields
    extracted = _llm_extract_query(text)
    
    # Load synonyms
    drug_synonyms = _load_drug_synonyms()
    disease_synonyms = _load_disease_synonyms()
    
    # Resolve drug name
    drug = extracted.get('drug')
    if drug:
        drug = _resolve_synonym(drug, drug_synonyms)
    
    # Resolve disease name
    disease = extracted.get('disease')
    if disease:
        disease = _resolve_synonym(disease, disease_synonyms)
    
    # Normalize region
    region = extracted.get('region', 'global')
    region = normalize_region(region) or 'GLOBAL'
    
    # Parse timespan
    timespan_days = _parse_timespan(extracted.get('timespan', '90 days'))
    
    # Determine granularity
    granularity = 'daily' if timespan_days <= 90 else 'weekly'
    
    parsed = {
        "drug": drug,
        "disease": disease,
        "region": region,
        "timespan_days": timespan_days,
        "granularity": granularity,
        "max_news": 10,
        "include_forums": True
    }
    
    logger.info(f"Parsed query: {parsed}")
    return parsed


def _llm_extract_query(text: str) -> Dict:
    """Use LLM to extract query fields."""
    prompt = f"""You are a query parser for pharmaceutical web intelligence.

Extract the following fields from the user query:
1. drug: Name of the drug/medication (or null if not mentioned)
2. disease: Name of the disease/condition (or null if not mentioned)
3. region: Geographic region (country name, ISO code, or "global")
4. timespan: Time period (e.g., "90 days", "3 months", "last 30 days")

RULES:
- Extract ONLY what is explicitly mentioned
- Return "null" for fields not mentioned
- For timespan, default to "90 days" if not specified
- Return valid JSON only

User Query: {text}

Return JSON:"""
    
    try:
        raw = llm.call(messages=[{"role": "user", "content": prompt}])
        if not isinstance(raw, str):
            raw = str(raw)
        
        # Parse JSON
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1:
            data = json.loads(raw[start:end+1])
            
            # Normalize null values
            for key in ['drug', 'disease', 'region', 'timespan']:
                if data.get(key) in [None, 'null', 'None', '']:
                    data[key] = None
            
            # Ensure drug/disease are strings, not lists (LLM can return lists)
            for key in ['drug', 'disease']:
                val = data.get(key)
                if isinstance(val, list):
                    data[key] = val[0] if val else None
                elif val is not None and not isinstance(val, str):
                    data[key] = str(val)
            
            return data
    except Exception as e:
        logger.warning(f"LLM extraction failed (using fallback parser): {e}")
        # Check if it's an API key error
        if "invalid_api_key" in str(e).lower() or "api key" in str(e).lower():
            logger.info("Tip: Set GROQ_API_KEY environment variable for better query parsing")
    
    # Fallback to regex-based extraction
    return _regex_extract_query(text)


def _regex_extract_query(text: str) -> Dict:
    """Fallback regex-based query extraction."""
    text_lower = text.lower()
    
    result = {
        "drug": None,
        "disease": None,
        "region": "global",
        "timespan": "90 days"
    }
    
    # Load synonyms for basic matching
    drug_synonyms = _load_drug_synonyms()
    disease_synonyms = _load_disease_synonyms()
    
    # Try to match drug names
    for canonical, synonyms in drug_synonyms.items():
        for synonym in synonyms:
            if synonym in text_lower:
                result['drug'] = canonical
                break
        if result['drug']:
            break
    
    # Try to match disease names
    for canonical, synonyms in disease_synonyms.items():
        for synonym in synonyms:
            if synonym in text_lower:
                result['disease'] = canonical
                break
        if result['disease']:
            break
    
    # Simple timespan patterns
    timespan_match = re.search(r'(?:last|past)\s+(\d+)\s+(day|week|month)s?', text_lower)
    if timespan_match:
        result['timespan'] = f"{timespan_match.group(1)} {timespan_match.group(2)}s"
    
    # Region patterns
    region_patterns = [
        r'\bin\s+([a-z]+(?:\s+[a-z]+)?)',  # "in India", "in United States"
        r'([a-z]+)\s+(?:market|region)',    # "India market", "US region"
    ]
    for pattern in region_patterns:
        match = re.search(pattern, text_lower)
        if match:
            result['region'] = match.group(1).strip()
            break
    
    return result


def _load_drug_synonyms() -> Dict[str, list]:
    """Load drug synonyms mapping."""
    try:
        import json
        module_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(module_dir, 'data', 'drug_synonyms.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load drug synonyms: {e}")
        return {}


def _load_disease_synonyms() -> Dict[str, list]:
    """Load disease synonyms mapping."""
    try:
        import json
        module_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(module_dir, 'data', 'disease_synonyms.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load disease synonyms: {e}")
        return {}


def _resolve_synonym(term, synonyms: Dict[str, list]) -> str:
    """Resolve term to canonical name using synonyms."""
    if not term:
        return term
    
    # Handle list inputs (LLM may return a list instead of a string)
    if isinstance(term, list):
        term = term[0] if term else None
        if not term:
            return None
    
    # Ensure term is a string
    if not isinstance(term, str):
        term = str(term)
    
    term_lower = term.lower()
    
    # Check if term is already canonical (a key in synonyms)
    if term_lower in synonyms:
        return term_lower
    
    # Search in synonym lists
    for canonical, synonym_list in synonyms.items():
        if term_lower in [s.lower() for s in synonym_list]:
            return canonical
    
    # Not found, return original
    return term


def _parse_timespan(timespan_str: str) -> int:
    """Parse timespan string to days."""
    if not timespan_str:
        return 90
    
    timespan_str = timespan_str.lower()
    
    # Extract number
    match = re.search(r'(\d+)', timespan_str)
    if not match:
        return 90
    
    num = int(match.group(1))
    
    # Determine unit
    if 'month' in timespan_str:
        return num * 30
    elif 'week' in timespan_str:
        return num * 7
    else:  # days or default
        return num


def _run_tools(query: Dict) -> Dict:
    """
    Orchestrate tool execution.
    
    Returns dict with raw tool outputs.
    """
    logger.info("Running web intelligence tools")
    
    # Build search keyword
    keyword = query.get('drug') or query.get('disease')
    if not keyword:
        raise ValueError("Must provide either drug or disease")
    
    region = query.get('region', 'GLOBAL')
    timespan_days = query.get('timespan_days', 90)
    max_news = query.get('max_news', 10)
    include_forums = query.get('include_forums', True)
    
    # 1. Fetch trends
    logger.info("Fetching trends data...")
    trends = trends_fetcher.get_trends(
        keyword=keyword,
        region=region,
        timespan_days=timespan_days,
        granularity=query.get('granularity', 'daily')
    )
    
    # 2. Fetch news
    logger.info("Fetching news articles...")
    news = news_fetcher.get_news(
        query=keyword,
        region=region,
        since_days=timespan_days,
        max_items=max_news
    )
    
    # 3. Fetch forums (optional)
    forums = []
    if include_forums:
        logger.info("Fetching forum data...")
        forums = forum_fetcher.get_forum_snippets(
            query=keyword,
            subreddit_list=None,  # Use defaults
            since_days=timespan_days,
            max_items=20
        )
    
    # 4. Preprocess and clean
    logger.info("Preprocessing data...")
    cleaned = preprocessor.clean_items(news, forums)
    news = cleaned['news']
    forums = cleaned['forums']
    
    # 5. Compute analytics signals
    logger.info("Computing signals...")
    signals = analytics_engine.compute_signals(trends, news, forums)
    
    return {
        "trends": trends,
        "news": news,
        "forums": forums,
        "signals": signals
    }


def _format_output(query: Dict, tool_outputs: Dict, summary: Dict) -> Dict:
    """
    Format final output for UI.
    
    Args:
        query: Parsed query
        tool_outputs: Raw tool outputs
        summary: LLM summary
        
    Returns:
        Final UI JSON
    """
    logger.info("Formatting output")
    
    return output_formatter.format_ui(
        summary_dict=summary,
        signals=tool_outputs['signals'],
        trends=tool_outputs['trends'],
        news=tool_outputs['news'],
        forums=tool_outputs['forums'],
        query=query
    )


def run(request_text: str) -> Dict:
    """
    Main entrypoint for Web Intelligence Agent.
    
    Args:
        request_text: Free-text user query
        
    Returns:
        Dict with:
        - status: "success" | "error"
        - data: UI JSON (if success)
        - message: Error message (if error)
    """
    print(f"\n{'='*60}")
    print(f"[WEB_INTELLIGENCE_AGENT] Starting execution")
    print(f"[WEB_INTELLIGENCE_AGENT] Query: {request_text}")
    print(f"{'='*60}")
    logger.info(f"[WEB_INTEL] Starting agent with prompt: {request_text}")
    
    try:
        # Step 1: Parse input
        print("[WEB_INTELLIGENCE_AGENT] Step 1: Parsing user input...")
        query = _parse_user_input(request_text)
        print(f"[WEB_INTELLIGENCE_AGENT] Parsed query: drug={query.get('drug')}, disease={query.get('disease')}, region={query.get('region')}")
        
        if not query.get('drug') and not query.get('disease'):
            print("[WEB_INTELLIGENCE_AGENT] ERROR: Could not extract drug/disease from query")
            return {
                "status": "error",
                "message": "Could not extract drug name or disease from query. "
                          "Please provide a drug name or disease/condition."
            }
        
        # Step 2: Run tools
        print("[WEB_INTELLIGENCE_AGENT] Step 2: Running intelligence tools...")
        tool_outputs = _run_tools(query)
        print(f"[WEB_INTELLIGENCE_AGENT] Tools completed - News: {len(tool_outputs.get('news', []))}, Forums: {len(tool_outputs.get('forums', []))}")
        
        # Step 3: LLM summarization
        print("[WEB_INTELLIGENCE_AGENT] Step 3: Generating LLM summary...")
        logger.info("Generating LLM summary...")
        context = {
            "query": query,
            "signals": tool_outputs['signals'],
            "news": tool_outputs['news'],
            "forums": tool_outputs['forums'],
            "trends": tool_outputs['trends']
        }
        summary = llm_summarizer.summarize(context)
        
        # Step 4: Format output
        print("[WEB_INTELLIGENCE_AGENT] Step 4: Formatting output...")
        ui_output = _format_output(query, tool_outputs, summary)
        
        print(f"[WEB_INTELLIGENCE_AGENT] Agent completed successfully!")
        print(f"[WEB_INTELLIGENCE_AGENT] Output contains: {list(ui_output.keys())}")
        print(f"{'='*60}\n")
        logger.info("[WEB_INTEL] Agent completed successfully")
        
        return {
            "status": "success",
            "data": ui_output
        }
        
    except Exception as e:
        print(f"[WEB_INTELLIGENCE_AGENT] ERROR: {str(e)}")
        logger.error(f"[WEB_INTEL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "message": "Web Intelligence currently unavailable — attempting reconnect",
            "error_details": str(e),
            "data": {
                "placeholder": True,
                "message": "Web Intelligence currently unavailable — attempting reconnect",
                "retry_available": True
            }
        }


# Alias for consistency with clinical_agent naming
run_web_intelligence_agent = run
