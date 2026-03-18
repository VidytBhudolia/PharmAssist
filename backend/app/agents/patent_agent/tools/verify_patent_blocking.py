"""
Tool 2: Patent Verification & Blocking Analysis

Scrapes Google Patents to verify if a patent blocks a drug-disease use case.
Uses LLM for claim interpretation with strict governance rules.
"""

from crewai.tools import tool
from crewai import LLM
import requests
import re
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Google Patents URL template
GOOGLE_PATENTS_URL = "https://patents.google.com/patent/{patent_number}"

# Headers for Google Patents scraping
SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# LLM initialized lazily to avoid import-time errors
_claim_llm = None

def _get_claim_llm():
    """Lazy initialization of LLM for claim analysis."""
    global _claim_llm
    if _claim_llm is None:
        _claim_llm = LLM(model="groq/llama-3.3-70b-versatile", temperature=0.1, max_tokens=1000)
    return _claim_llm

# Claim type to blocking severity mapping
SEVERITY_MAP = {
    "COMPOSITION": "ABSOLUTE",
    "METHOD_OF_TREATMENT": "STRONG", 
    "FORMULATION": "WEAK",
    "PROCESS": "WEAK",
    "OTHER": "WEAK",
}


def _scrape_google_patent(patent_number: str) -> Dict[str, Any]:
    """
    Scrape patent data from Google Patents.
    
    Extracts:
    - Title
    - Assignee (Current Assignee)
    - Expected expiry (with fallback calculation)
    - Claims text (independent claim 1)
    - CPC codes
    - Family/continuation info
    - Jurisdiction
    
    CRITICAL: expectedExpiry must NEVER be null for active patents.
    If scraping fails, compute fallback: filing_date + 20 years
    """
    # Normalize patent number for URL
    clean_num = patent_number.upper().replace(" ", "").replace("-", "")
    if not clean_num.startswith("US"):
        clean_num = f"US{clean_num}"
    
    url = GOOGLE_PATENTS_URL.format(patent_number=clean_num)
    
    try:
        resp = requests.get(url, headers=SCRAPE_HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text
        
        result = {
            "patentNumber": clean_num,
            "url": url,
            "scraped": True,
        }
        
        # Extract title from <meta name="DC.title">
        title_match = re.search(r'<meta name="DC\.title" content="([^"]+)"', html)
        result["title"] = title_match.group(1) if title_match else ""
        
        # Extract assignee - look for "Current Assignee" section
        assignee_match = re.search(
            r'Current Assignee.*?<dd[^>]*>([^<]+)</dd>',
            html, re.DOTALL | re.IGNORECASE
        )
        if assignee_match:
            result["assignee"] = assignee_match.group(1).strip()
        else:
            # Fallback: look for assignee meta tag
            assignee_meta = re.search(r'<meta name="DC\.contributor" content="([^"]+)"', html)
            result["assignee"] = assignee_meta.group(1) if assignee_meta else "Unknown"
        
        # ====================================================================
        # EXPIRY EXTRACTION - CRITICAL SECTION
        # ====================================================================
        # Google Patents uses both "Expected expiration" and "Anticipated expiration"
        # HTML structure: <time datetime="YYYY-MM-DD">YYYY-MM-DD</time> followed by <span>Anticipated expiration</span>
        # CRITICAL: The time tag comes BEFORE the label, but may have other tags in between
        expiry_date = None
        expiry_confidence = "HIGH"
        expiry_source = "scraped"
        
        # Pattern 1: Find "Anticipated expiration" or "Expected expiration" label first,
        # then look BACKWARDS for the nearest <time> tag (robust approach)
        expiry_label_pos = -1
        for label in ["Anticipated expiration", "Expected expiration"]:
            pos = html.find(label)
            if pos != -1:
                expiry_label_pos = pos
                break
        
        if expiry_label_pos != -1:
            # Look backwards up to 300 chars for <time datetime="YYYY-MM-DD">
            search_start = max(0, expiry_label_pos - 300)
            snippet = html[search_start:expiry_label_pos]
            time_match = re.search(r'<time[^>]*datetime="(\d{4}-\d{2}-\d{2})"', snippet)
            if time_match:
                expiry_date = time_match.group(1)
                expiry_confidence = "HIGH"
                expiry_source = "scraped"
        
        # Pattern 2: Fallback - search forward from expiration label (old format)
        if not expiry_date:
            expiry_match = re.search(
                r'(Expected expiration|Anticipated expiration)[^0-9]{0,100}(\d{4}-\d{2}-\d{2})',
                html, re.IGNORECASE
            )
            if expiry_match:
                expiry_date = expiry_match.group(2)
                expiry_confidence = "MEDIUM"
                expiry_source = "scraped"
        
        # ====================================================================
        # FALLBACK EXPIRY CALCULATION - NEVER RETURN NULL
        # ====================================================================
        # If scraping failed, compute expiry from filing/priority date
        # Standard patent term: priority_date + 20 years (35 U.S.C. § 154)
        if not expiry_date:
            # Extract filing date from meta tags or HTML
            filing_date = None
            
            # Try <meta name="DC.date"> first (publication date)
            date_meta = re.search(r'<meta name="DC\.date" content="(\d{4}-\d{2}-\d{2})"', html)
            if date_meta:
                filing_date = date_meta.group(1)
            
            # Try priority date from priority claims section
            if not filing_date:
                priority_match = re.search(
                    r'priority[^0-9]{0,100}(\d{4}-\d{2}-\d{2})',
                    html, re.IGNORECASE
                )
                if priority_match:
                    filing_date = priority_match.group(1)
            
            # Try application filing date
            if not filing_date:
                filing_match = re.search(
                    r'filing[^0-9]{0,100}(\d{4}-\d{2}-\d{2})',
                    html, re.IGNORECASE
                )
                if filing_match:
                    filing_date = filing_match.group(1)
            
            # Compute expiry: filing_date + 20 years
            if filing_date:
                try:
                    filing_dt = datetime.strptime(filing_date, "%Y-%m-%d")
                    # Add 20 years to get expiry (standard utility patent term)
                    expiry_dt = filing_dt.replace(year=filing_dt.year + 20)
                    expiry_date = expiry_dt.strftime("%Y-%m-%d")
                    expiry_confidence = "LOW"
                    expiry_source = "computed_from_filing_date"
                except Exception as e:
                    # If computation fails, use a very distant date with warning
                    expiry_date = "2099-12-31"
                    expiry_confidence = "VERY_LOW"
                    expiry_source = "fallback_default"
        
        # Store expiry results
        result["expectedExpiry"] = expiry_date
        result["expiryConfidence"] = expiry_confidence
        result["expirySource"] = expiry_source
        
        # If still no expiry found, add warning but don't set to null
        if not expiry_date or expiry_confidence == "VERY_LOW":
            result["expiryWarning"] = "Could not reliably extract or compute expiry date"
        
        # Extract claims - look for claims section
        claims_match = re.search(
            r'<section itemprop="claims"[^>]*>(.*?)</section>',
            html, re.DOTALL
        )
        claim_text = None
        if claims_match:
            claims_html = claims_match.group(1)
            # Strategy 1: Find first independent claim by class
            claim1_match = re.search(
                r'<div[^>]*class="claim"[^>]*>(.*?)</div>',
                claims_html, re.DOTALL
            )
            if claim1_match:
                claim_text = re.sub(r'<[^>]+>', ' ', claim1_match.group(1))
                claim_text = re.sub(r'\s+', ' ', claim_text).strip()
            
            # Strategy 2: Try claim-text span
            if not claim_text:
                claim_span_match = re.search(
                    r'<span[^>]*class="claim-text"[^>]*>(.*?)</span>',
                    claims_html, re.DOTALL
                )
                if claim_span_match:
                    claim_text = re.sub(r'<[^>]+>', ' ', claim_span_match.group(1))
                    claim_text = re.sub(r'\s+', ' ', claim_text).strip()
            
            # Strategy 3: Get ALL independent claims (marked with class="claim" and num="1" or first few claims)
            if not claim_text:
                all_claims = re.findall(
                    r'<div[^>]*class="claim[^"]*"[^>]*>(.*?)</div>',
                    claims_html, re.DOTALL
                )
                if all_claims:
                    # Get first 3 claims for broader context
                    combined = " ".join(all_claims[:3])
                    claim_text = re.sub(r'<[^>]+>', ' ', combined)
                    claim_text = re.sub(r'\s+', ' ', claim_text).strip()
        
        # Strategy 4: Try abstract as additional context if no claims found
        if not claim_text:
            abstract_match = re.search(
                r'<section itemprop="abstract"[^>]*>(.*?)</section>',
                html, re.DOTALL
            )
            if abstract_match:
                abstract_text = re.sub(r'<[^>]+>', ' ', abstract_match.group(1))
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                if abstract_text and len(abstract_text) > 20:
                    claim_text = f"[ABSTRACT] {abstract_text}"
            
            # Also try meta description
            if not claim_text:
                desc_match = re.search(r'<meta name="DC\.description" content="([^"]+)"', html)
                if desc_match and len(desc_match.group(1)) > 20:
                    claim_text = f"[ABSTRACT] {desc_match.group(1)}"
        
        result["claim1"] = claim_text[:2500] if claim_text else None
        
        # Extract CPC codes
        cpc_matches = re.findall(r'<meta scheme="cpc" content="([^"]+)"', html)
        result["cpcCodes"] = list(set(cpc_matches)) if cpc_matches else []
        
        # Detect continuations/family - look for "Family" or continuation mentions
        has_family = bool(re.search(
            r'(Family|Continuation|Divisional|Parent Application)',
            html, re.IGNORECASE
        ))
        result["hasContinuations"] = has_family
        
        # Extract jurisdiction from patent number
        if clean_num.startswith("US"):
            result["jurisdiction"] = "US"
        elif clean_num.startswith("EP"):
            result["jurisdiction"] = "EP"
        elif clean_num.startswith("WO"):
            result["jurisdiction"] = "WO"
        else:
            result["jurisdiction"] = "UNKNOWN"
        
        # Check if patent is expired based on expiry date
        if result.get("expectedExpiry"):
            try:
                expiry_dt = datetime.strptime(result["expectedExpiry"][:10], "%Y-%m-%d")
                result["isExpired"] = expiry_dt < datetime.now()
            except:
                result["isExpired"] = None
        else:
            result["isExpired"] = None
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            "patentNumber": patent_number,
            "scraped": False,
            "error": f"Failed to fetch Google Patents: {str(e)}",
        }
    except Exception as e:
        return {
            "patentNumber": patent_number,
            "scraped": False,
            "error": f"Scraping error: {str(e)}",
        }


def _analyze_claim_with_llm(
    claim_text: str,
    drug: str,
    disease: str,
    title: str = "",
    cpc_codes: list = None,
    assignee: str = "",
) -> Dict[str, Any]:
    """
    Use LLM to analyze if claim blocks the drug-disease use.
    
    LLM Governance Rules:
    - Temperature 0.1 (highly deterministic)
    - Must make a definitive blocking determination (true/false) whenever possible
    - Use title, CPC codes, and assignee as supplementary context
    - Return null for blocksUse ONLY if genuinely impossible to determine
    """
    # Build context from all available information
    context_parts = []
    
    if claim_text:
        context_parts.append(f"CLAIM TEXT (from patent document):\n{claim_text[:2000]}")
    
    if title:
        context_parts.append(f"PATENT TITLE: {title}")
    
    if assignee and assignee != "Unknown":
        context_parts.append(f"PATENT ASSIGNEE: {assignee}")
    
    if cpc_codes:
        # Filter to pharma-relevant CPC codes
        pharma_codes = [c for c in cpc_codes if any(c.upper().startswith(p) for p in ["A61K", "A61P", "C07"])]
        if pharma_codes:
            context_parts.append(f"RELEVANT CPC CODES: {', '.join(pharma_codes[:10])}")
    
    if not context_parts:
        return {
            "claimType": "OTHER",
            "blocksUse": None,
            "confidence": "LOW",
            "reasoning": "No patent data available for analysis",
        }
    
    combined_context = "\n\n".join(context_parts)
    has_claim_text = bool(claim_text)
    
    prompt = f"""You are a senior pharmaceutical patent analyst with deep expertise in Freedom-to-Operate (FTO) assessments. Analyze whether this patent blocks the use of a specific drug for a specific disease.

TARGET DRUG: {drug}
TARGET DISEASE/INDICATION: {disease}

{combined_context}

ANALYSIS INSTRUCTIONS:
1. CLAIM TYPE CLASSIFICATION - Classify as exactly ONE of:
   - COMPOSITION: Claims covering the drug compound itself, its salts, polymorphs, or pharmaceutical compositions containing it
   - METHOD_OF_TREATMENT: Claims covering the use/method of treating the specific disease with the drug
   - FORMULATION: Claims covering specific dosage forms, delivery systems, or formulation techniques
   - PROCESS: Claims covering manufacturing or synthesis methods
   - OTHER: Claims not fitting above categories

2. BLOCKING DETERMINATION - You MUST make a definitive determination:
   - true: The patent claims cover or would be infringed by using "{drug}" to treat "{disease}". This includes:
     * Composition claims that broadly cover the drug molecule
     * Method claims that cover treating the disease with this drug class
     * Formulation claims for the drug that would be necessary to use
   - false: The patent claims do NOT cover using "{drug}" for "{disease}" because:
     * The claims are directed to a different drug/compound
     * The claims cover a different therapeutic indication
     * The claims are too narrow to encompass the intended use
   - null: ONLY if there is genuinely insufficient information to make any determination (e.g., no claim text AND no title information)

   IMPORTANT: Do NOT default to null/uncertain. Pharma patents found through drug+disease keyword searches are LIKELY relevant. 
   If the patent title mentions the drug or disease, that is strong evidence of relevance.
   If CPC codes include A61K (pharma compositions) or A61P (therapeutic activity), the patent is pharma-relevant.
   Make your best expert judgment - a "likely blocks" should be true, a "probably doesn't block" should be false.

3. CONFIDENCE LEVEL:
   - HIGH: Clear claim language directly mentions drug and/or disease
   - MEDIUM: Claim language is broad but reasonably covers the drug-disease combination
   - LOW: Limited information available but determination made on best available evidence

{"4. Quote specific claim language supporting your determination." if has_claim_text else "4. Explain your reasoning based on the available patent information."}

Return ONLY valid JSON (no markdown, no backticks, no explanation outside JSON):
{{
    "claimType": "COMPOSITION|METHOD_OF_TREATMENT|FORMULATION|PROCESS|OTHER",
    "blocksUse": true|false|null,
    "confidence": "HIGH|MEDIUM|LOW",
    "reasoning": "Brief explanation (1-2 sentences)"
}}"""

    try:
        response = _get_claim_llm().call(messages=[{"role": "user", "content": prompt}])
        
        # Parse JSON from response - try multiple patterns
        result = None
        
        # Pattern 1: Find JSON block (handles nested braces)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Pattern 2: Simple JSON extraction
        if result is None:
            json_match = re.search(r'\{.*?\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        
        # Pattern 3: Extract field by field as fallback
        if result is None:
            result = _extract_fields_from_text(response)
        
        if result:
            # Validate and normalize claim type
            valid_claim_types = {"COMPOSITION", "METHOD_OF_TREATMENT", "FORMULATION", "PROCESS", "OTHER"}
            if result.get("claimType") not in valid_claim_types:
                result["claimType"] = _infer_claim_type_from_context(
                    claim_text or "", title, cpc_codes or []
                )
            
            # Normalize blocksUse - convert string representations
            blocks_val = result.get("blocksUse")
            if isinstance(blocks_val, str):
                blocks_val = blocks_val.lower().strip()
                if blocks_val in ("true", "yes", "blocking"):
                    result["blocksUse"] = True
                elif blocks_val in ("false", "no", "non-blocking", "non_blocking"):
                    result["blocksUse"] = False
                elif blocks_val in ("null", "none", "uncertain", "unknown"):
                    result["blocksUse"] = None
            
            if "confidence" not in result or result["confidence"] not in ("HIGH", "MEDIUM", "LOW"):
                result["confidence"] = "MEDIUM" if has_claim_text else "LOW"
            
            return result
        
        # All parsing failed
        return {
            "claimType": _infer_claim_type_from_context(claim_text or "", title, cpc_codes or []),
            "blocksUse": _infer_blocking_from_title(title, drug, disease),
            "confidence": "LOW",
            "reasoning": "LLM response parsing failed; determination based on title/metadata heuristics",
        }
        
    except Exception as e:
        print(f"[PATENT VERIFY] LLM analysis error: {e}")
        return {
            "claimType": _infer_claim_type_from_context(claim_text or "", title, cpc_codes or []),
            "blocksUse": _infer_blocking_from_title(title, drug, disease),
            "confidence": "LOW",
            "reasoning": f"LLM analysis failed: {str(e)}; determination based on heuristics",
        }


def _extract_fields_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON fields from LLM response text when JSON parsing fails."""
    result = {}
    
    # Extract claimType
    ct_match = re.search(r'"claimType"\s*:\s*"(COMPOSITION|METHOD_OF_TREATMENT|FORMULATION|PROCESS|OTHER)"', text, re.IGNORECASE)
    if ct_match:
        result["claimType"] = ct_match.group(1).upper()
    
    # Extract blocksUse
    bu_match = re.search(r'"blocksUse"\s*:\s*(true|false|null)', text, re.IGNORECASE)
    if bu_match:
        val = bu_match.group(1).lower()
        result["blocksUse"] = True if val == "true" else False if val == "false" else None
    
    # Extract confidence
    conf_match = re.search(r'"confidence"\s*:\s*"(HIGH|MEDIUM|LOW)"', text, re.IGNORECASE)
    if conf_match:
        result["confidence"] = conf_match.group(1).upper()
    
    # Extract reasoning
    reason_match = re.search(r'"reasoning"\s*:\s*"([^"]+)"', text, re.DOTALL)
    if reason_match:
        result["reasoning"] = reason_match.group(1)
    
    return result if result else None


def _infer_claim_type_from_context(
    claim_text: str, title: str, cpc_codes: list
) -> str:
    """Infer claim type from available context when LLM fails."""
    text = (claim_text + " " + title).lower()
    
    # Check for composition indicators
    composition_keywords = ["compound", "composition", "comprising", "salt", "polymorph",
                           "crystal", "pharmaceutical composition", "active ingredient"]
    if any(kw in text for kw in composition_keywords):
        return "COMPOSITION"
    
    # Check for method of treatment indicators
    method_keywords = ["method of treating", "treating", "treatment of", "use of",
                       "administered to", "effective amount", "therapeutically effective"]
    if any(kw in text for kw in method_keywords):
        return "METHOD_OF_TREATMENT"
    
    # Check for formulation indicators
    formulation_keywords = ["formulation", "dosage form", "tablet", "capsule", "injection",
                           "sustained release", "controlled release", "extended release"]
    if any(kw in text for kw in formulation_keywords):
        return "FORMULATION"
    
    # Check for process indicators
    process_keywords = ["process for", "method of preparing", "synthesis", "manufacturing",
                       "producing", "reacting"]
    if any(kw in text for kw in process_keywords):
        return "PROCESS"
    
    # Check CPC codes
    for cpc in (cpc_codes or []):
        cpc_upper = cpc.upper()
        if cpc_upper.startswith("A61K"):
            return "COMPOSITION"
        elif cpc_upper.startswith("A61P"):
            return "METHOD_OF_TREATMENT"
        elif cpc_upper.startswith("C07"):
            return "COMPOSITION"
    
    return "OTHER"


def _infer_blocking_from_title(title: str, drug: str, disease: str) -> Optional[bool]:
    """
    Infer blocking status from patent title when LLM fails.
    Uses keyword matching as a conservative heuristic.
    """
    if not title:
        return None
    
    title_lower = title.lower()
    drug_lower = drug.lower() if drug else ""
    disease_lower = disease.lower() if disease else ""
    
    drug_in_title = drug_lower and drug_lower in title_lower
    disease_in_title = disease_lower and disease_lower in title_lower
    
    # If BOTH drug and disease appear in title, likely blocks
    if drug_in_title and disease_in_title:
        return True
    
    # If drug appears in title (composition claim likely), probably blocks
    if drug_in_title:
        return True
    
    # If only disease appears, it might be for a different drug
    if disease_in_title and not drug_in_title:
        return False
    
    # Neither drug nor disease in title - probably doesn't block
    return False


@tool("verify_patent_blocking")
def verify_patent_blocking(
    patent_number: str,
    drug: str,
    disease: str,
    jurisdiction: str = "US"
) -> Dict[str, Any]:
    """
    Verify if a patent blocks a specific drug-disease use case.
    
    Scrapes Google Patents for claims, expiry, and assignee, then uses
    LLM to classify claim type and determine blocking status.
    
    Args:
        patent_number: Patent to verify (e.g., "US11723898")
        drug: Target drug name
        disease: Target disease/indication
        jurisdiction: Jurisdiction filter (default "US")
    
    Returns:
        Verification result with:
        - patent: Patent number
        - assignee: Current patent owner
        - expectedExpiry: Expiry date from Google Patents
        - claimType: COMPOSITION, METHOD_OF_TREATMENT, etc.
        - blocksUse: true/false/null
        - blockingSeverity: ABSOLUTE/STRONG/WEAK
        - confidence: HIGH/MEDIUM/LOW
        - hasContinuations: Boolean flag for patent family
        - evidence: Claim excerpt and reasoning
    """
    # Step 1: Scrape Google Patents
    scraped = _scrape_google_patent(patent_number)
    
    if not scraped.get("scraped"):
        return {
            "patent": patent_number,
            "error": scraped.get("error", "Scraping failed"),
            "blocksUse": None,
            "confidence": "LOW",
            "requiresManualReview": True,
        }
    
    # Step 2: Check jurisdiction filter
    if scraped.get("jurisdiction") != jurisdiction and jurisdiction != "ALL":
        return {
            "patent": patent_number,
            "assignee": scraped.get("assignee"),
            "expectedExpiry": scraped.get("expectedExpiry"),
            "jurisdiction": scraped.get("jurisdiction"),
            "skipped": True,
            "reason": f"Patent jurisdiction {scraped.get('jurisdiction')} does not match filter {jurisdiction}",
            "blocksUse": False,
            "confidence": "HIGH",
        }
    
    # Step 3: Check if already expired
    if scraped.get("isExpired"):
        return {
            "patent": patent_number,
            "assignee": scraped.get("assignee"),
            "expectedExpiry": scraped.get("expectedExpiry"),
            "jurisdiction": scraped.get("jurisdiction"),
            "claimType": "N/A",
            "blocksUse": False,
            "blockingSeverity": "NONE",
            "confidence": "HIGH",
            "status": "EXPIRED",
            "hasContinuations": scraped.get("hasContinuations", False),
            # Removed evidence field from output
        }
    
    # Step 4: Analyze claim with LLM (pass all available context)
    claim_analysis = _analyze_claim_with_llm(
        scraped.get("claim1"),
        drug,
        disease,
        title=scraped.get("title", ""),
        cpc_codes=scraped.get("cpcCodes", []),
        assignee=scraped.get("assignee", ""),
    )
    
    # Step 5: Determine blocking severity
    claim_type = claim_analysis.get("claimType", "OTHER")
    blocking_severity = SEVERITY_MAP.get(claim_type, "WEAK")
    
    # Step 6: Build final result
    # NOTE: Evidence is kept internally for audit/debugging but NOT included in return
    # to avoid exposing verbose claim excerpts in the UI
    result = {
        "patent": patent_number,
        "url": scraped.get("url"),
        "title": scraped.get("title"),
        "assignee": scraped.get("assignee", "Unknown"),
        "expectedExpiry": scraped.get("expectedExpiry"),
        "expiryConfidence": scraped.get("expiryConfidence", "MEDIUM"),
        "expirySource": scraped.get("expirySource", "unknown"),
        "isExpired": scraped.get("isExpired", False),
        "jurisdiction": scraped.get("jurisdiction", "US"),
        "claimType": claim_type,
        "blocksUse": claim_analysis.get("blocksUse"),
        "blockingSeverity": blocking_severity if claim_analysis.get("blocksUse") else "NONE",
        "confidence": claim_analysis.get("confidence", "LOW"),
        "hasContinuations": scraped.get("hasContinuations", False),
        "cpcCodes": scraped.get("cpcCodes", []),
        # Removed: "evidence" field - kept only for internal audit
        "_auditEvidence": {
            "claimExcerpt": (scraped.get("claim1") or "")[:500],
            "reasoning": claim_analysis.get("reasoning", ""),
        },
    }
    
    # Flag if manual review needed
    if claim_analysis.get("blocksUse") is None or claim_analysis.get("confidence") == "LOW":
        result["requiresManualReview"] = True
    
    # Flag if expiry confidence is low (computed vs scraped)
    if scraped.get("expiryConfidence") in ("LOW", "VERY_LOW"):
        result["requiresManualReview"] = True
        result["expiryWarning"] = scraped.get("expiryWarning", "Expiry date computed from filing date, not scraped from Google Patents")
    
    # Add continuation warning
    if scraped.get("hasContinuations"):
        result["continuationWarning"] = "Patent family detected - protection may extend beyond listed expiry"
    
    return result
