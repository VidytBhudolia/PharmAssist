from crewai.tools import tool
from crewai import LLM
import json
from app.apis.iqvia_api import fetch_statista_search


llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=200)


# --------------------------------------------------
# Generate multiple optimized Statista queries
# --------------------------------------------------
def _generate_statista_queries(user_prompt: str) -> list[str]:
    prompt = f"""
You are an expert Statista search optimizer.

From the user request below, generate 3 high-quality Statista search queries
specifically optimized for finding INFOGRAPHICS about pharmaceutical/healthcare markets.

Rules:
- Each query should be 2-4 words
- Avoid the word "statistics" 
- Include market-related terms like "market", "sales", "revenue", "forecast"
- Prefer patterns like:
  "breast cancer market"
  "oncology drug sales"
  "pharmaceutical market forecast"
  "cancer treatment market"
  "healthcare spending"
- Return a JSON array with exactly 3 strings

User request: {user_prompt}

Return only JSON array.
"""
    raw = llm.call([{"role": "user", "content": prompt}])
    try:
        # Extract JSON from response
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1:
            return json.loads(raw[start : end + 1])
        return json.loads(raw)
    except Exception as e:
        print(f"[Statista] Query generation failed: {e}")
        # Fallback: extract main topic from prompt
        words = user_prompt.lower().split()
        base_queries = []
        for word in words:
            if len(word) > 3 and word not in [
                "market",
                "analysis",
                "give",
                "show",
                "what",
            ]:
                base_queries.append(f"{word} market")
                break
        return base_queries if base_queries else ["pharmaceutical market"]


def _build_statista_image_url(item: dict) -> str | None:
    """Construct a direct Statista image URL from a SERP result.

    Statista provides embeddable images at:
    https://www.statista.com/graphic/1/{contentId}/{slug}.jpg
    where slug is derived from urlPath. We fall back to the CDN pattern when
    the slug is unavailable.
    """

    content_id = item.get("contentId")
    if not content_id:
        return None

    url_path = item.get("urlPath") or ""
    slug = url_path.strip("/").split("/")[-1] if url_path else None
    if slug:
        return f"https://www.statista.com/graphic/1/{content_id}/{slug}.jpg"

    content_type = item.get("contentType", "")
    if content_type == "infographic":
        return f"https://cdn.statcdn.com/Infographic/images/normal/{content_id}.jpeg"
    return f"https://cdn.statcdn.com/Statistic/images/{content_id}.jpeg"


def _fetch_and_filter_infographics(
    query: str, include_premium: bool = False, include_statistics: bool = True
) -> list[dict]:
    """
    Fetch infographics from Statista and filter results.

    Args:
        query: Search query
        include_premium: If True, include premium content when no free ones found
        include_statistics: If True, also include statistic charts (not just infographics)

    Returns:
        List of infographic/statistic dictionaries with CDN image URLs
    """
    try:
        # Don't filter by content_type in API - it doesn't work as expected
        # Instead, we filter the results ourselves
        raw_response = fetch_statista_search(
            query=query, content_type=None, page=1, sort="relevance"
        )

        response_data = json.loads(raw_response)
        search_results = response_data.get("searchResponse", {}).get("results", [])

        print(f"[Statista] Raw results for '{query}': {len(search_results)} items")

    except Exception as e:
        print(f"[ERROR] Statista API call failed for '{query}': {e}")
        return []

    free_items = []
    premium_items = []

    # Content types that have visual charts we can display
    # "infographic" = actual infographic images
    # "statistic" = chart/graph visualizations
    visual_content_types = {"infographic", "statistic"}

    for item in search_results:
        content_type = item.get("contentType", "")

        # Only process visual content types (infographics and statistics)
        if content_type not in visual_content_types:
            continue

        content_id = item.get("contentId")
        if not content_id:
            continue

        image_url = _build_statista_image_url(item)
        if not image_url:
            continue

        item_data = {
            "type": "image",
            "content": image_url,
            "title": item.get("title", ""),
            "subtitle": item.get("subtitle", ""),
            "description": item.get("description", ""),
            "url": f"https://www.statista.com{item.get('urlPath', '')}",
            "contentId": content_id,
            "contentType": content_type,
            "premium": item.get("premium", True),
        }

        if not item.get("premium", True):
            free_items.append(item_data)
        else:
            premium_items.append(item_data)

    print(
        f"[Statista] Query '{query}': {len(free_items)} free, {len(premium_items)} premium visual items"
    )

    # Return free items if available
    if free_items:
        return free_items

    # If no free items and include_premium is True, return top premium ones
    # (limited to 5 to avoid overwhelming the UI)
    if include_premium and premium_items:
        print(
            f"[Statista] No free items found, using top {min(5, len(premium_items))} premium as fallback"
        )
        return premium_items[:5]

    return []


@tool("fetch_statista_infographics")
def fetch_statista_infographics(user_prompt: str) -> dict:
    """
    Fetches Statista infographics for pharmaceutical/healthcare market analysis.

    Process:
    1. Generate optimized search queries from user prompt
    2. Query Statista's search API for each query
    3. Filter for infographic content type
    4. Prefer free (non-premium) infographics
    5. Construct CDN image URLs from contentId
    6. Return structured results with image URLs
    """

    print(f"[Statista] Starting infographic fetch for: {user_prompt}")

    if not user_prompt:
        return {
            "status": "no_data",
            "results": [],
            "message": "No user prompt received.",
        }

    # Generate multiple search queries for better coverage
    queries = _generate_statista_queries(user_prompt)
    if not queries:
        queries = (
            [user_prompt.split()[0] + " market"]
            if user_prompt.split()
            else ["pharmaceutical market"]
        )

    print(f"[Statista] Generated queries: {queries}")

    all_infographics = []
    seen_content_ids = set()
    queries_tried = []

    # Try each query, collecting unique infographics
    for query in queries:
        queries_tried.append(query)

        # First try to get free infographics
        infographics = _fetch_and_filter_infographics(query, include_premium=False)

        for info in infographics:
            content_id = info.get("contentId")
            if content_id and content_id not in seen_content_ids:
                seen_content_ids.add(content_id)
                all_infographics.append(info)

        # Stop if we have enough infographics
        if len(all_infographics) >= 6:
            break

    # If no free infographics found after all queries, try with premium fallback
    if not all_infographics and queries:
        print(f"[Statista] No free infographics found, trying with premium fallback")
        for query in queries[:1]:  # Only try first query with premium
            infographics = _fetch_and_filter_infographics(query, include_premium=True)
            for info in infographics:
                content_id = info.get("contentId")
                if content_id and content_id not in seen_content_ids:
                    seen_content_ids.add(content_id)
                    all_infographics.append(info)
            if all_infographics:
                break

    print(f"[Statista] Total unique infographics collected: {len(all_infographics)}")

    if all_infographics:
        return {
            "status": "success",
            "query_used": ", ".join(queries_tried),
            "results": all_infographics[:8],  # Limit to 8 infographics
            "count": len(all_infographics[:8]),
        }

    return {
        "status": "no_data",
        "query_used": ", ".join(queries_tried),
        "results": [],
        "message": "No Statista infographics found for this query. Try a broader healthcare or market term.",
    }
