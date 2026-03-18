"""
Tool 3: FTO Decision Engine

Deterministic FTO scoring based on verified patent portfolio.
Uses rule-based scoring matrix - LLM only for summary generation.

═══════════════════════════════════════════════════════════════════════════════
POLICY & DESIGN RATIONALE
═══════════════════════════════════════════════════════════════════════════════

SCORING PHILOSOPHY:
- All decisions are rule-based and deterministic (no LLM-based scoring)
- Conservative approach: when in doubt, flag for manual review
- Per-patent score cap (12) prevents numeric explosion, NOT legal severity
- A single COMPOSITION claim can require licensing even at MODERATE status

RISK BAND SEMANTICS (0-100 Normalized Index):
- CLEAR (0):       No blocking patents identified
- LOW (1-25):      Minor concerns, proceed with monitoring
- MODERATE (26-50): Some blocking patents, counsel recommended
- HIGH (51-75):    Significant blocking, licensing likely needed
- CRITICAL (76-100): Multiple severe blockers, licensing required

FTO STATUS MAPPING:
- CLEAR   → "CLEAR"
- LOW     → "NEEDS_MONITORING"
- MODERATE → "AT_RISK"
- HIGH    → "BLOCKED"
- CRITICAL → "BLOCKED"

IMPORTANT: Score capping does NOT diminish legal risk!
- A COMPOSITION patent with continuation scores 16 → capped at 12 → MODERATE
- But MODERATE + COMPOSITION still means "licensing may be required"
- Recommended actions reflect claim severity, not just numeric score

UNCERTAINTY HANDLING:
- Missing expiry date = uncertainty penalty (+3), NOT assumed long-term protection
- Scraping errors = highest uncertainty (+5) - cannot verify patent details
- Ambiguous claims = moderate uncertainty (+3) - LLM could not determine blocking
- Low confidence = minor uncertainty (+2) - LLM analysis had low certainty

CONTINUATION RISK:
- Patent families extend protection beyond listed expiry dates
- Continuation penalty (+2) accounts for potential derivative patents
- COMPOSITION claims with continuations are especially concerning

CONFIDENCE LEVELS:
- HIGH: All data verified, no uncertain patents
- MEDIUM: 1 uncertain patent OR some blocking patents have MEDIUM confidence
- LOW: 2+ uncertain patents OR critical data missing

═══════════════════════════════════════════════════════════════════════════════
"""

from crewai.tools import tool
from crewai import LLM
from typing import Dict, Any, List
from datetime import datetime

# Import new modules for enhanced output
from .normalizer import normalize_raw_score, get_band_description, BAND_TO_FTO_STATUS
from .formatter import format_patent_entry, format_patent_entry_expanded, build_visualization_payload, build_summary_texts
from .recommender import recommend_actions
from .llm_prompts import (
    build_executive_prompt,
    build_business_prompt,
    build_legal_prompt,
    generate_fallback_executive,
    generate_fallback_business,
    generate_fallback_legal,
)

# Scoring weights (deterministic)
CLAIM_TYPE_WEIGHTS = {
    "COMPOSITION": 7,
    "METHOD_OF_TREATMENT": 5,
    "FORMULATION": 3,
    "PROCESS": 2,
    "OTHER": 1,
}

EXPIRY_WEIGHTS = {
    "gt_10_years": 5,   # > 10 years remaining
    "5_to_10_years": 3, # 5-10 years remaining
    "lt_5_years": 1,    # < 5 years remaining
}

CONFIDENCE_WEIGHTS = {
    "HIGH": 2,
    "MEDIUM": 1,
    "LOW": 0,
}

# Risk bands (using new thresholds)
RISK_BANDS = {
    "CLEAR": (0, 0),
    "LOW": (1, 25),
    "MODERATE": (26, 50),
    "HIGH": (51, 75),
    "CRITICAL": (76, 100),
}

# LLM initialized lazily to avoid import-time errors
_summary_llm = None
_llm_available = None

def _get_summary_llm():
    """Lazy initialization of LLM for summary generation.
    
    Returns None if LLM unavailable (API key missing, network error, etc.)
    Falls back to deterministic summary generation.
    """
    global _summary_llm, _llm_available
    
    # If we've already determined LLM is unavailable, return None
    if _llm_available is False:
        return None
    
    # If LLM is already initialized, return it
    if _summary_llm is not None:
        return _summary_llm
    
    # Try to initialize LLM
    try:
        import os
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key")
        
        if not api_key:
            _llm_available = False
            return None
        
        _summary_llm = LLM(model="groq/llama-3.3-70b-versatile", temperature=0.3, max_tokens=500)
        _llm_available = True
        return _summary_llm
    except Exception as e:
        # LLM initialization failed (invalid key, network error, etc.)
        _llm_available = False
        return None


def _calculate_years_to_expiry(expiry_date: str) -> float:
    """Calculate years remaining until patent expiry.
    
    Returns:
        float: Years until expiry (>=0)
        None: Expiry date is missing or invalid (triggers uncertainty penalty)
    """
    if not expiry_date:
        return None  # Missing expiry = uncertainty, not long-term risk
    
    try:
        expiry_dt = datetime.strptime(expiry_date[:10], "%Y-%m-%d")
        days = (expiry_dt - datetime.now()).days
        return max(0, days / 365.25)
    except:
        return None  # Invalid expiry = uncertainty


def _classify_patent(verification: Dict) -> str:
    """
    Classify patent into FTO category.
    
    Categories:
    - EXPIRED: No longer enforceable
    - ACTIVE_BLOCKING: Active and blocks the use
    - ACTIVE_NON_BLOCKING: Active but does not block
    - UNCERTAIN: Could not determine (ONLY for genuine scraping failures)
    
    IMPORTANT: Reduced UNCERTAIN classifications by:
    - Treating error/skipped patents with heuristic data as NON_BLOCKING if confidence exists
    - Using claim type as a signal when blocksUse is ambiguous
    """
    # Check for hard errors with no data at all
    if verification.get("error") and not verification.get("claimType"):
        return "UNCERTAIN"
    
    # Skipped patents (jurisdiction mismatch) are non-blocking
    if verification.get("skipped"):
        return "ACTIVE_NON_BLOCKING"
    
    # Check if expired
    if verification.get("status") == "EXPIRED":
        return "EXPIRED"
    
    expiry = verification.get("expectedExpiry")
    if expiry:
        years = _calculate_years_to_expiry(expiry)
        if years is not None and years <= 0:
            return "EXPIRED"
    
    # Check blocking status
    blocks_use = verification.get("blocksUse")
    if blocks_use is True:
        return "ACTIVE_BLOCKING"
    elif blocks_use is False:
        return "ACTIVE_NON_BLOCKING"
    else:
        # blocksUse is None - check if we have enough context to infer
        # If confidence is MEDIUM or HIGH, the analysis was done but couldn't decide
        # If claim type is known, we have some data
        confidence = verification.get("confidence", "LOW")
        claim_type = verification.get("claimType", "OTHER")
        
        # If we have an error (scraping failed completely), truly uncertain
        if verification.get("error"):
            return "UNCERTAIN"
        
        # If claim type was identified but blocking is unknown, 
        # classify based on claim severity as a conservative approach
        if claim_type in ("COMPOSITION", "METHOD_OF_TREATMENT"):
            # Conservative: these claim types are likely blocking if they exist
            # for the drug-disease combination
            return "ACTIVE_BLOCKING"
        elif claim_type in ("FORMULATION", "PROCESS"):
            # These are weaker claims - treat as non-blocking unless confirmed
            return "ACTIVE_NON_BLOCKING"
        
        return "UNCERTAIN"


def _score_blocking_patent(verification: Dict) -> tuple:
    """
    Calculate risk score for a blocking patent.
    
    Scoring matrix:
    - Claim type: COMPOSITION +7, METHOD_OF_TREATMENT +5, etc.
    - Expiry: >10yr +5, 5-10yr +3, <5yr +1, missing +3 (uncertainty)
    - Confidence: HIGH +2, MEDIUM +1, LOW +0
    - Continuation risk: +2 if patent family exists
    
    Returns:
        tuple: (score: int, notes: List[str])
    """
    score = 0
    notes = []
    
    # Claim type weight
    claim_type = verification.get("claimType", "OTHER")
    score += CLAIM_TYPE_WEIGHTS.get(claim_type, 1)
    
    # Expiry weight
    years = _calculate_years_to_expiry(verification.get("expectedExpiry"))
    if years is None:
        # Missing expiry = uncertainty penalty (not long-term risk)
        score += 3
        notes.append(f"{verification.get('patent')}: Expiry missing – uncertainty penalty applied")
    elif years > 10:
        score += EXPIRY_WEIGHTS["gt_10_years"]
    elif years >= 5:
        score += EXPIRY_WEIGHTS["5_to_10_years"]
    else:
        score += EXPIRY_WEIGHTS["lt_5_years"]
    
    # Confidence weight
    confidence = verification.get("confidence", "LOW")
    score += CONFIDENCE_WEIGHTS.get(confidence, 0)
    
    # Continuation risk (patent families extend protection)
    if verification.get("hasContinuations"):
        score += 2
        notes.append(f"{verification.get('patent')}: Continuation risk applied")
    
    # Cap per-patent score at 12 to prevent single patent domination
    if score > 12:
        notes.append(f"{verification.get('patent')}: Score capped at 12 (was {score})")
        score = 12
    
    return score, notes


def _determine_overall_confidence(uncertain_patents: List[Dict], blocking_patents: List[Dict]) -> str:
    """Determine overall confidence level using graduated logic.
    
    Confidence reflects data quality and certainty of analysis:
    - HIGH: All patents verified, no uncertainties, all blocking patents have HIGH confidence
    - MEDIUM: 1 uncertain patent OR any blocking patent has MEDIUM/LOW confidence  
    - LOW: 2+ uncertain patents (significant data quality issues)
    
    Args:
        uncertain_patents: List of patents that could not be classified
        blocking_patents: List of active blocking patents
    
    Returns:
        Confidence level: "HIGH", "MEDIUM", or "LOW"
    """
    if len(uncertain_patents) >= 2:
        # Multiple uncertain patents = low confidence in overall assessment
        return "LOW"
    elif len(uncertain_patents) == 1:
        # Single uncertain patent = medium confidence
        return "MEDIUM"
    elif any(p.get("confidence") == "LOW" for p in blocking_patents):
        # Any blocking patent with low confidence
        return "MEDIUM"
    elif any(p.get("confidence") == "MEDIUM" for p in blocking_patents):
        # Any blocking patent with medium confidence
        return "MEDIUM"
    else:
        # All blocking patents have high confidence, no uncertain patents
        return "HIGH"


def _determine_fto_status(band: str) -> str:
    """Map risk band to FTO status using canonical mapping."""
    return BAND_TO_FTO_STATUS.get(band, "AT_RISK")


def _get_recommended_actions(fto_status: str, blocking_patents: List[Dict]) -> List[str]:
    """Generate recommended actions based on FTO status and blocking patents.
    
    DEPRECATED: Use recommend_actions() from recommender.py instead.
    This function is kept for backwards compatibility only.
    
    IMPORTANT: Actions reflect both FTO status AND claim severity.
    A COMPOSITION claim at MODERATE status may still require licensing.
    """
    actions = []
    
    # Check for composition claims upfront (absolute blockers)
    has_composition = any(p.get("claimType") == "COMPOSITION" for p in blocking_patents)
    
    if fto_status == "CLEAR":
        actions.append("Proceed with development - no blocking patents identified")
    
    elif fto_status == "NEEDS_MONITORING":
        actions.append("Proceed with caution - monitor identified patents")
        actions.append("Consider freedom-to-operate opinion from patent counsel")
    
    elif fto_status == "AT_RISK":
        actions.append("Seek detailed FTO opinion from patent counsel")
        actions.append("Evaluate licensing opportunities")
        actions.append("Consider design-around strategies")
        
        # COMPOSITION claims may require licensing even at AT_RISK
        if has_composition:
            actions.append("WARNING: Composition claims present - design-around may not be feasible")
        
        # Check for near-expiry options
        for p in blocking_patents:
            years = _calculate_years_to_expiry(p.get("expectedExpiry"))
            if years is not None and years < 3:
                actions.append(f"Wait for {p.get('patent')} expiry ({p.get('expectedExpiry')[:10] if p.get('expectedExpiry') else 'unknown'})")
                break
    
    elif fto_status == "BLOCKED":
        actions.append("Licensing required before proceeding")
        actions.append("Evaluate alternative indications or formulations")
        actions.append("Consider design-around or indication shift")
        
        if has_composition:
            actions.append("WARNING: Composition claims present - design-around may not be feasible")
    
    return actions


def _generate_summary(drug: str, disease: str, fto_status: str, blocking_patents: List[Dict]) -> str:
    """Generate human-readable summary (LLM optional - falls back to deterministic).
    
    The actual FTO decision is deterministic and rule-based.
    This summary is for human readability only.
    """
    if not blocking_patents:
        return f"No blocking patents identified for {drug} in {disease}. FTO appears clear for US jurisdiction."
    
    # Try LLM if available
    llm = _get_summary_llm()
    if llm:
        try:
            patent_list = "\n".join([
                f"- {p.get('patent')}: {p.get('claimType')} claim, expires {p.get('expectedExpiry', 'unknown')}"
                for p in blocking_patents[:5]
            ])
            
            prompt = f"""Summarize this FTO assessment in 2-3 sentences. Do NOT make recommendations - just state facts.

Drug: {drug}
Disease: {disease}
FTO Status: {fto_status}
Blocking Patents:
{patent_list}

Write a brief factual summary:"""
            
            response = llm.call(messages=[{"role": "user", "content": prompt}])
            return response.strip()
        except Exception as e:
            # LLM call failed, fall through to deterministic summary
            pass
    
    # Fallback: Generate deterministic summary from patent data
    blocking_count = len(blocking_patents)
    claim_types = ", ".join(set(p.get("claimType", "OTHER") for p in blocking_patents))
    earliest_expiry = min(
        (p.get("expectedExpiry", "9999-12-31") for p in blocking_patents if p.get("expectedExpiry")),
        default="unknown"
    )
    
    return f"FTO assessment for {drug} in {disease} indicates {fto_status}. {blocking_count} blocking patent(s) identified ({claim_types}), earliest expiring {earliest_expiry}."


@tool("fto_decision_engine")
def fto_decision_engine(
    patent_verifications: List[Dict[str, Any]],
    drug: str,
    disease: str,
    jurisdiction: str = "US",
    total_found_in_api: int = None,
) -> Dict[str, Any]:
    """
    Generate FTO decision based on verified patent portfolio.
    
    Uses deterministic scoring matrix - NO LLM for decisions.
    Enhanced output includes normalized 0-100 risk index, formatted patent entries,
    multi-layer summaries, and actionable recommendations.
    
    Args:
        patent_verifications: Array of verify_patent_blocking outputs
        drug: Target drug name
        disease: Target disease/indication
        jurisdiction: FTO jurisdiction scope (default "US")
        total_found_in_api: Total patents returned by API (for display purposes)
    
    Returns:
        Enhanced FTO decision with:
        - ftoRiskIndex: Normalized 0-100 risk score
        - ftoRiskBand: LOW/MODERATE/HIGH/CRITICAL
        - rawScore: Legacy internal sum (for audits)
        - blockingPatents: Human-friendly table entries
        - recommendedActions: Actionable with feasibility ratings
        - summary: Multi-layer (executive/business/legal)
        - visualizationPayload: Frontend-ready chart data
    """
    num_patents = len(patent_verifications) if patent_verifications else 0
    # Use total_found_in_api for display, num_patents for scoring
    patents_found_display = total_found_in_api if total_found_in_api is not None else num_patents
    
    # Handle empty input
    if not patent_verifications:
        normalized = normalize_raw_score(0, 0)
        return {
            "drug": drug,
            "disease": disease,
            "jurisdiction": jurisdiction,
            # New canonical fields
            "ftoStatus": "CLEAR",
            "ftoDate": None,
            "normalizedRiskInternal": 0,
            "patentsFound": total_found_in_api if total_found_in_api is not None else 0,
            "blockingPatentsSummary": {
                "count": 0,
                "claimTypeCounts": {},
            },
            "blockingPatents": [],
            "recommendedActions": [{
                "action": "Proceed with Standard Monitoring",
                "reason": "No patents analyzed - verify discovery results",
                "feasibility": "HIGH",
                "nextStep": "Verify patent search parameters"
            }],
            "summary": {
                "executive": f"No patents found for {drug} in {disease}. FTO appears clear pending manual verification.",
                "business": f"No blocking patents identified for {drug} in {disease}. Proceed with standard IP monitoring.",
                "legal": "No patents analyzed. Recommend manual verification of patent landscape."
            },
            "visualizationPayload": build_visualization_payload([], normalized, [], [], [], []),
            "expandedResults": {
                "nonBlockingPatents": [],
                "expiredPatents": [],
                "uncertainPatents": [],
            },
            "confidence": "LOW",
            "analysisDate": datetime.now().isoformat(),
            "disclaimer": "This is an automated assessment. Consult qualified patent counsel for legal advice.",
        }
    
    # Step 1: Classify all patents
    blocking_patents = []
    expired_patents = []
    non_blocking_patents = []
    uncertain_patents = []
    
    for v in patent_verifications:
        category = _classify_patent(v)
        
        if category == "EXPIRED":
            expired_patents.append(v)
        elif category == "ACTIVE_BLOCKING":
            blocking_patents.append(v)
        elif category == "ACTIVE_NON_BLOCKING":
            non_blocking_patents.append(v)
        else:
            uncertain_patents.append(v)
    
    # Step 2: Score blocking patents
    total_score = 0
    scored_blocking = []
    scoring_notes = []
    
    for p in blocking_patents:
        score, notes = _score_blocking_patent(p)
        total_score += score
        scoring_notes.extend(notes)
        scored_blocking.append({
            **p,
            "riskScore": score,
        })
    
    # Step 2b: Add differentiated penalties for uncertain patents (conservative)
    for p in uncertain_patents:
        penalty = 0
        
        # Differentiate uncertainty causes
        if p.get("error"):
            penalty = 5
            scoring_notes.append(f"{p.get('patent')}: Scraping error – high uncertainty penalty (+5)")
        elif p.get("blocksUse") is None:
            penalty = 3
            scoring_notes.append(f"{p.get('patent')}: Ambiguous claim – moderate uncertainty penalty (+3)")
        elif p.get("confidence") == "LOW":
            penalty = 2
            scoring_notes.append(f"{p.get('patent')}: Low confidence – minor uncertainty penalty (+2)")
        
        total_score += penalty
    
    # Step 3: Normalize score to 0-100 index
    normalized = normalize_raw_score(total_score, num_patents)
    normalized_risk_internal = normalized["normalizedRiskInternal"]
    fto_band = normalized["band"]
    
    # Map band to FTO status using canonical mapping
    fto_status = BAND_TO_FTO_STATUS.get(fto_band, "AT_RISK")
    
    # Step 4: Find FTO date (earliest date when freedom is achieved)
    fto_date = None
    if blocking_patents:
        expiry_dates = []
        for p in blocking_patents:
            exp = p.get("expectedExpiry")
            if exp:
                try:
                    expiry_dates.append(datetime.strptime(exp[:10], "%Y-%m-%d"))
                except:
                    pass
        
        if expiry_dates:
            latest_expiry = max(expiry_dates)
            fto_date = latest_expiry.strftime("%Y-%m-%d")
    
    # Step 5: Generate actionable recommendations using new recommender (top 3 only)
    recommended_actions = recommend_actions(
        verifications=patent_verifications,
        fto_index=normalized_risk_internal,
        band=fto_band,
        blocking_patents=scored_blocking,
    )
    
    # Step 6: Determine overall confidence
    confidence = _determine_overall_confidence(uncertain_patents, blocking_patents)
    
    # Step 7: Format patent entries for display
    # Blocking patents: use compact format (no evidence, no internal scores)
    formatted_blocking = [format_patent_entry(p) for p in scored_blocking]
    # Non-blocking/expired/uncertain: use expanded format for expandedResults
    formatted_non_blocking = [format_patent_entry_expanded(p) for p in non_blocking_patents]
    formatted_expired = [format_patent_entry_expanded(p) for p in expired_patents]
    formatted_uncertain = [format_patent_entry_expanded(p) for p in uncertain_patents]
    
    # Step 8: Build multi-layer summaries
    summary = build_summary_texts(
        verifications=patent_verifications,
        normalized_result=normalized,
        drug=drug,
        disease=disease,
        blocking_patents=scored_blocking,
        earliest_freedom_date=fto_date,
        recommended_actions=recommended_actions,
    )
    
    # Step 9: Build visualization payload (includes pieData and claimTypeCounts)
    viz_payload = build_visualization_payload(
        verifications=patent_verifications,
        normalized_result=normalized,
        blocking_patents=scored_blocking,
        non_blocking_patents=non_blocking_patents,
        expired_patents=expired_patents,
        uncertain_patents=uncertain_patents,
    )
    
    # Step 10: Build blockingPatentsSummary with claimTypeCounts
    claim_type_counts = {}
    for p in scored_blocking:
        ct = p.get("claimType", "OTHER")
        claim_type_counts[ct] = claim_type_counts.get(ct, 0) + 1
    
    blocking_patents_summary = {
        "count": len(formatted_blocking),
        "claimTypeCounts": claim_type_counts,
    }
    
    # Step 11: Add continuation warnings
    continuation_warnings = []
    for p in blocking_patents:
        if p.get("hasContinuations"):
            continuation_warnings.append(
                f"{p.get('patent')}: Patent family may extend protection beyond {p.get('expectedExpiry', 'listed expiry')}"
            )
    
    return {
        # Core decision fields (canonical schema)
        "drug": drug,
        "disease": disease,
        "jurisdiction": jurisdiction,
        "ftoStatus": fto_status,
        "ftoDate": fto_date,  # Renamed from earliestFreedomDate
        "normalizedRiskInternal": normalized_risk_internal,  # Internal use only, not for UI
        "patentsFound": patents_found_display,  # Total from API, not analyzed count
        
        # Blocking patents summary with claimTypeCounts
        "blockingPatentsSummary": blocking_patents_summary,
        
        # Formatted blocking patents (display-ready, no evidence/internal scores)
        "blockingPatents": formatted_blocking,
        
        # Recommendations (top 3 only, with nextStep singular)
        "recommendedActions": recommended_actions,
        
        # Confidence in overall assessment
        "confidence": confidence,
        
        # Multi-layer summaries
        "summary": summary,
        
        # Visualization data (includes pieData with integer counts)
        "visualizationPayload": viz_payload,
        
        # Expanded results for drill-down (non-blocking patents go here)
        "expandedResults": {
            "nonBlockingPatents": formatted_non_blocking,
            "expiredPatents": formatted_expired,
            "uncertainPatents": formatted_uncertain,
        },
        
        # Warnings
        "continuationWarnings": continuation_warnings if continuation_warnings else None,
        
        # Metadata
        "analysisDate": datetime.now().isoformat(),
        "disclaimer": "This is an automated assessment. Consult qualified patent counsel for legal advice.",
    }
