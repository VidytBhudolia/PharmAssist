"""
Tool 1: Patent Discovery

Searches USPTO to find candidate patents for a drug-disease combination.
Returns top 10 most relevant patents ranked by keyword + CPC matching.
NO LLM - pure data retrieval.

IMPORTANT: This tool returns ONLY valid patent/publication numbers that can be
resolved on Google Patents. Raw application numbers are NEVER returned.

Patent Types:
- "granted": Patented Case → US########B2 format (from patentIdentificationBag)
- "published": Pre-Grant Publications → US20########A1 format (from publicationBag)
"""

from crewai.tools import tool
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

USPTO_SEARCH_URL = "https://data.uspto.gov/ui/patent/applications/search"

# Browser-mimicking headers (required for JSON response)
USPTO_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en;q=0.7",
    "content-type": "application/json",
    "origin": "https://data.uspto.gov",
    "referer": "https://data.uspto.gov/patent-file-wrapper/search",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/144.0.0.0",
}

# USPTO filter configurations (correct format for their API)
USPTO_FILTER_GRANTED = {
    "field": "applicationMetaData.applicationStatusDescriptionText",
    "value": "Patented Case"  # Single value, not "values" array
}

USPTO_FILTER_PUBLISHED = {
    "field": "applicationMetaData.publicationCategoryBag",
    "value": "Pre-Grant Publications"
}


def _calculate_relevance_score(patent: Dict, drug: str, disease: str) -> float:
    """
    Score patent relevance based on multiple signals.
    Higher scores = more relevant to the drug-disease combination.
    
    Scoring breakdown:
    1. Drug name in title (+30)
    2. Disease name in title (+25)
    3. Drug name in any field (+15 if not already in title)
    4. CPC class A61K/A61P pharma match (+15)
    5. CPC class C07 chemistry match (+10)
    6. Recency bonus (+10 max)
    7. Granted patent bonus (+5 over published applications)
    """
    score = 0.0
    drug_lower = (drug or "").lower()
    disease_lower = (disease or "").lower()
    
    # Get fields from nested or flat structure
    meta = patent.get("applicationMetaData", patent)
    title = (meta.get("inventionTitle") or meta.get("title") or "").lower()
    cpc_codes = meta.get("cpcClassificationBag") or meta.get("cpcCodes") or []
    
    # Also check assignee for pharma company names
    assignee = ""
    applicants = meta.get("applicantBag", [])
    if applicants and isinstance(applicants, list):
        assignee = (applicants[0].get("applicantNameText") or "").lower()
    
    # Keyword matches in title (strongest signal)
    drug_in_title = drug_lower and drug_lower in title
    disease_in_title = disease_lower and disease_lower in title
    
    if drug_in_title:
        score += 30
    if disease_in_title:
        score += 25
    
    # Both drug AND disease in title is very strong signal — bonus
    if drug_in_title and disease_in_title:
        score += 10
    
    # CPC pharma class boost
    has_a61k = False
    has_a61p = False
    has_c07 = False
    for cpc in cpc_codes:
        cpc_str = str(cpc).upper()
        if cpc_str.startswith("A61K"):
            has_a61k = True
        elif cpc_str.startswith("A61P"):
            has_a61p = True
        elif cpc_str.startswith("C07"):
            has_c07 = True
    
    if has_a61k:
        score += 15
    if has_a61p:
        score += 10
    if has_c07:
        score += 10
    
    # Recency bonus
    filing_date = meta.get("filingDate")
    if filing_date:
        try:
            dt = datetime.fromisoformat(filing_date.replace("Z", "")[:10])
            years_old = (datetime.now() - dt).days / 365.25
            if years_old < 5:
                score += 10
            elif years_old < 10:
                score += 5
        except:
            pass
    
    # Granted patent bonus (issued patents are more threatening than applications)
    status_text = meta.get("applicationStatusDescriptionText", "")
    if "patented case" in status_text.lower():
        score += 5
    
    return score


def _extract_patent_number(patent: Dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract valid patent/publication number from USPTO response.
    
    CRITICAL: Never fabricate patent numbers from applicationNumberText!
    
    Returns:
        Tuple of (patent_number, patent_type) where:
        - patent_number: Google Patents-compatible number or None
        - patent_type: "granted", "published", or None
    
    Sources:
    - Granted patents: applicationMetaData.patentNumber (for Patented Case status)
      Format: US########B2
    - Published apps: applicationMetaData.earliestPublicationNumber
      Format: US20########A1
    """
    meta = patent.get("applicationMetaData", {})
    patent_num = None
    patent_type = None
    
    # Priority 1: Check for GRANTED patent via patentNumber field
    # This exists when applicationStatusDescriptionText == "Patented Case"
    raw_patent_num = meta.get("patentNumber")
    if raw_patent_num:
        # Format: Ensure US prefix and B2 suffix for granted patents
        raw_num = str(raw_patent_num).replace("/", "").replace("-", "")
        if raw_num.startswith("US"):
            patent_num = raw_num
        else:
            patent_num = f"US{raw_num}"
        # Add B2 suffix if not present (standard utility patent grant)
        if not any(patent_num.endswith(s) for s in ["B1", "B2", "B3"]):
            patent_num = f"{patent_num}B2"
        patent_type = "granted"
    
    # Priority 2: Check patentIdentificationBag (alternative location)
    if not patent_num:
        patent_id_bag = meta.get("patentIdentificationBag", [])
        if isinstance(patent_id_bag, list) and len(patent_id_bag) > 0:
            raw_num = patent_id_bag[0].get("patentNumber", "")
            if raw_num:
                raw_num = str(raw_num).replace("/", "").replace("-", "")
                if raw_num.startswith("US"):
                    patent_num = raw_num
                else:
                    patent_num = f"US{raw_num}"
                if not any(patent_num.endswith(s) for s in ["B1", "B2", "B3"]):
                    patent_num = f"{patent_num}B2"
                patent_type = "granted"
    
    # Priority 3: Check for PUBLISHED application via earliestPublicationNumber
    # Format: US20XXXXXXXAX
    if not patent_num:
        earliest_pub = meta.get("earliestPublicationNumber", "")
        if earliest_pub and earliest_pub.startswith("US"):
            patent_num = earliest_pub
            patent_type = "published"
    
    # Priority 4: Check publicationBag (alternative location)
    if not patent_num:
        publication_bag = meta.get("publicationBag", [])
        if isinstance(publication_bag, list) and len(publication_bag) > 0:
            pub_num = publication_bag[0].get("publicationNumber", "")
            if pub_num:
                patent_num = str(pub_num).replace("/", "").replace("-", "")
                if not patent_num.startswith("US"):
                    patent_num = f"US{patent_num}"
                patent_type = "published"
    
    # DO NOT fallback to applicationNumberText - that's a raw application number
    # which is NOT resolvable on Google Patents and would cause downstream failures
    
    return patent_num, patent_type


def _normalize_patent(patent: Dict, patent_num: str, patent_type: str) -> Dict:
    """
    Normalize patent to consistent output schema.
    
    Args:
        patent: Raw USPTO response object
        patent_num: Pre-validated Google Patents-compatible number
        patent_type: "granted" or "published"
    
    Returns:
        Normalized patent dict with patentNumber, patentType, title, assignee, filingDate
    """
    meta = patent.get("applicationMetaData", {})
    
    # Get assignee from applicantBag or direct field
    assignee = "Unknown"
    applicants = meta.get("applicantBag", [])
    if applicants:
        # Try applicantNameText first, then applicantName
        assignee = (
            applicants[0].get("applicantNameText") or
            applicants[0].get("applicantName") or
            "Unknown"
        )
    else:
        assignee = meta.get("assigneeName") or patent.get("assignee") or "Unknown"
    
    # Normalize filing date to YYYY-MM-DD
    filing_date = meta.get("filingDate") or ""
    if filing_date:
        # Handle ISO format with time component
        if "T" in filing_date:
            filing_date = filing_date[:10]
        # Ensure YYYY-MM-DD format
        filing_date = filing_date[:10]
    
    return {
        "patentNumber": patent_num,
        "patentType": patent_type,  # "granted" or "published"
        "title": meta.get("inventionTitle") or meta.get("title") or "",
        "assignee": assignee,
        "filingDate": filing_date,
    }


def _build_filters(status: str) -> List[Dict]:
    """
    Build USPTO API filters based on status parameter.
    
    Args:
        status: "granted", "published", or "both"
    
    Returns:
        List of filter objects for USPTO API
    
    Note: Instead of using API filters (which have format issues), we filter
    client-side based on the patent type extracted from each record.
    This is more reliable than depending on USPTO's inconsistent filter API.
    """
    # Return empty filters - we filter client-side for reliability
    # The USPTO API filter format is inconsistent and causes 400 errors
    return []


@tool("discover_patents")
def discover_patents(
    drug: str,
    disease: str,
    limit: int = 10,
    status: str = "granted"
) -> Dict[str, Any]:
    """
    Find candidate patents related to a drug-disease combination.
    
    Args:
        drug: Drug/molecule name (e.g., "metformin")
        disease: Disease/indication (e.g., "diabetes")
        limit: Max patents to return (default 10)
        status: Filter by patent status (default "granted")
            - "granted": Only issued patents (Patented Case) → US########B2
            - "published": Only published applications → US20########A1
            - "both": Both granted patents and published applications
    
    Returns:
        Dict with:
        - patents: List of {patentNumber, patentType, title, assignee, filingDate, relevanceScore}
        - query: Search query used
        - totalFound: Total matches in USPTO
        - returnedCount: Number of valid patents returned
        
    Note:
        Only returns patents with valid Google Patents-compatible numbers.
        Raw application numbers are never returned.
    """
    if not drug and not disease:
        return {"error": "Must provide drug or disease", "patents": []}
    
    # Validate status parameter
    if status not in ("granted", "published", "both"):
        return {"error": f"Invalid status '{status}'. Must be 'granted', 'published', or 'both'", "patents": []}
    
    # Build query
    terms = [t for t in [drug, disease] if t]
    query = " AND ".join(terms)
    
    # Build filters based on status
    filters = _build_filters(status)
    
    # Match USPTO's expected payload structure exactly
    payload = {
        "q": query,
        "filters": filters,
        "rangeFilters": [],
        "pagination": {
            "offset": 0,
            "limit": 100  # Fetch more to account for filtering
        },
        "sort": [
            {
                "field": "applicationMetaData.filingDate",
                "order": "Desc"
            }
        ],
        "facets": [
            "applicationMetaData.applicationTypeLabelName",
            "applicationMetaData.publicationCategoryBag",
            "applicationMetaData.applicationStatusDescriptionText",
            "applicationMetaData.entityStatusData.businessEntityStatusCategory",
            "applicationMetaData.groupArtUnitNumber"
        ]
    }
    
    try:
        resp = requests.post(USPTO_SEARCH_URL, headers=USPTO_HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # USPTO returns data in "patentFileWrapperDataBag"
        results = data.get("patentFileWrapperDataBag") or data.get("results") or data.get("docs") or []
        total_count = data.get("count") or data.get("totalCount") or len(results)
        
        if not results:
            return {
                "patents": [],
                "query": query,
                "drug": drug,
                "disease": disease,
                "status": status,
                "totalFound": total_count,
                "returnedCount": 0,
                "jurisdiction": "US",
                "note": f"No {status} patents found matching the search criteria"
            }
        
        # Extract valid patents and score them
        # CRITICAL: Only include patents with valid patent/publication numbers
        scored_patents = []
        skipped_count = 0
        
        for patent_data in results:
            # Extract valid patent number (never uses applicationNumberText)
            patent_num, patent_type = _extract_patent_number(patent_data)
            
            # Skip if no valid patent number found
            if not patent_num:
                skipped_count += 1
                continue
            
            # For "both" status, we already have mixed results
            # For specific status, verify the type matches
            if status == "granted" and patent_type != "granted":
                continue
            if status == "published" and patent_type != "published":
                continue
            
            # Calculate relevance score
            score = _calculate_relevance_score(patent_data, drug, disease)
            scored_patents.append((patent_data, patent_num, patent_type, score))
        
        # Sort by relevance score (descending)
        scored_patents.sort(key=lambda x: x[3], reverse=True)
        
        # Take top N and normalize
        patents = []
        for patent_data, patent_num, patent_type, score in scored_patents[:min(limit, 25)]:
            p = _normalize_patent(patent_data, patent_num, patent_type)
            p["relevanceScore"] = round(score, 1)
            patents.append(p)
        
        return {
            "patents": patents,
            "query": query,
            "drug": drug,
            "disease": disease,
            "status": status,
            "totalFound": total_count,
            "returnedCount": len(patents),
            "skippedCount": skipped_count,  # Records without valid patent numbers
            "jurisdiction": "US",
            "note": f"Data from USPTO Patent File Wrapper. Only {status} patents with valid Google Patents-compatible numbers returned.",
        }
    
    except requests.exceptions.RequestException as e:
        return {"error": f"USPTO request failed: {str(e)}", "patents": [], "query": query}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "patents": [], "query": query}
