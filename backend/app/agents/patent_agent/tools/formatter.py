"""
FTO Output Formatter

Transforms raw patent analysis data into human-friendly, UI-ready output.

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT CHANGES (Jan 2026):
- All keys use camelCase (no underscores)
- "freedomDate" renamed to "ftoDate" (YYYY-MM-DD format)
- "evidence" field REMOVED from blockingPatents
- "confidence" field REMOVED from blockingPatents  
- Per-patent "riskBand" added: CLEAR/LOW/MODERATE/HIGH/CRITICAL
- normalizedRiskInternal is for INTERNAL SORTING ONLY (not displayed)
- blockingPatentsSummary includes claimTypeCounts
- pieData ensures labels are strings and counts are integers (no NaN)
═══════════════════════════════════════════════════════════════════════════════

RESPONSIBILITIES:
- Humanize field names (snake_case → Title Case)
- Format patent entries for display (riskBand, reason, NO evidence/confidence)
- Build visualization payload for frontend charts
- Generate multi-layer summary texts (executive, business, legal)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .normalizer import get_band_color, get_band_description, PER_PATENT_CAP, normalize_patent_risk


# ============================================================================
# FIELD NAME HUMANIZATION
# ============================================================================

SPECIAL_LABELS = {
    "fto": "FTO",
    "ftoStatus": "FTO Status",
    "ftoRiskIndex": "FTO Risk Index",
    "ftoRiskBand": "Risk Band",
    "nct_id": "NCT ID",
    "patent": "Patent Number",
    "blocksUse": "Blocks Use",
    "claimType": "Claim Type",
    "expectedExpiry": "Expected Expiry",
    "hasContinuations": "Has Continuations",
    "riskScore": "Risk Score",
    "api": "API",
    "ip": "IP",
}


def humanize_field_name(internal_name: str) -> str:
    """
    Convert internal field names to human-readable labels.
    
    Examples:
        "expectedExpiry" → "Expected Expiry"
        "blocksUse" → "Blocks Use"
        "claim_type" → "Claim Type"
    """
    if not internal_name:
        return ""
    
    # Check special cases first
    if internal_name in SPECIAL_LABELS:
        return SPECIAL_LABELS[internal_name]
    
    # Convert camelCase to Title Case
    result = ""
    for i, char in enumerate(internal_name):
        if char.isupper() and i > 0:
            result += " "
        result += char
    
    # Also handle snake_case
    result = result.replace("_", " ")
    
    return result.title()


# ============================================================================
# PATENT ENTRY FORMATTING
# ============================================================================

STATUS_LABELS = {
    True: "Blocking",
    False: "Non-blocking",
    None: "Uncertain",
    "EXPIRED": "Expired",
}

CLAIM_TYPE_LABELS = {
    "COMPOSITION": "Composition",
    "METHOD_OF_TREATMENT": "Method of Treatment",
    "FORMULATION": "Formulation",
    "PROCESS": "Process",
    "OTHER": "Other",
}


def format_patent_entry(verification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a single patent verification result for display.
    
    ═══════════════════════════════════════════════════════════════════════════
    OUTPUT SCHEMA (Jan 2026 - Canonical Format):
    ═══════════════════════════════════════════════════════════════════════════
    
    Input (verification object from verify_patent_blocking):
        {
            "patent": "US12345678B2",
            "title": "Metformin compositions...",
            "assignee": "Company X",
            "expectedExpiry": "2039-01-31",
            "blocksUse": true,
            "claimType": "COMPOSITION",
            "hasContinuations": true,
            "riskScore": 12  # if scored
        }
    
    Output (display-friendly format - CANONICAL):
        {
            "patentNumber": "US12345678B2",   # Renamed from "patent"
            "claimType": "Composition",       # Title case
            "expiry": "2039-01-31",           # Renamed from expectedExpiry, YYYY-MM-DD
            "riskBand": "CRITICAL",           # CLEAR/LOW/MODERATE/HIGH/CRITICAL
            "reason": "Composition claim covers API",  # Short 6-12 words
            "hasContinuations": true
        }
    
    REMOVED from output:
    - evidence (not needed in UI)
    - confidence (internal only)
    - normalizedRisk (internal sorting only - kept in separate field if needed)
    - sourceUrl (moved to expandedResults only)
    - requiresManualReview (internal flag)
    - title, assignee (moved to expandedResults only)
    ═══════════════════════════════════════════════════════════════════════════
    """
    patent_num = verification.get("patent", "Unknown")
    blocks_use = verification.get("blocksUse")
    claim_type = verification.get("claimType", "OTHER")
    has_continuations = verification.get("hasContinuations", False)
    expiry = verification.get("expectedExpiry")
    raw_score = verification.get("riskScore", 0)
    
    # Determine status for internal logic
    if verification.get("status") == "EXPIRED" or _is_expired(expiry):
        status = "Expired"
    else:
        status = STATUS_LABELS.get(blocks_use, "Uncertain")
    
    # Get riskBand using normalized score
    risk_result = normalize_patent_risk(raw_score, blocks_use, status)
    risk_band = risk_result["riskBand"]
    
    # Build SHORT human-readable reason (6-12 words per spec)
    reason = _build_short_reason(blocks_use, claim_type, has_continuations)
    
    # Format expiry to YYYY-MM-DD (required format)
    formatted_expiry = _format_date_strict(expiry)
    
    # INFO: Removed evidence field from blocking patents per spec
    print(f"[FORMATTER] INFO: Removed evidence field from patent {patent_num}")
    
    return {
        "patentNumber": patent_num,
        "patentUrl": _build_source_url(patent_num),
        "claimType": CLAIM_TYPE_LABELS.get(claim_type, claim_type),
        "expiry": formatted_expiry,
        "riskBand": risk_band,
        "reason": reason,
        "hasContinuations": has_continuations,
    }


def format_patent_entry_expanded(verification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format patent for expandedResults (includes more detail).
    Used for nonBlockingPatents and internal audit data.
    """
    patent_num = verification.get("patent", "Unknown")
    blocks_use = verification.get("blocksUse")
    claim_type = verification.get("claimType", "OTHER")
    has_continuations = verification.get("hasContinuations", False)
    expiry = verification.get("expectedExpiry")
    raw_score = verification.get("riskScore", 0)
    
    if verification.get("status") == "EXPIRED" or _is_expired(expiry):
        status = "Expired"
    else:
        status = STATUS_LABELS.get(blocks_use, "Uncertain")
    
    risk_result = normalize_patent_risk(raw_score, blocks_use, status)
    
    return {
        "patentNumber": patent_num,
        "patentUrl": _build_source_url(patent_num),
        "title": verification.get("title", "Unknown Title"),
        "assignee": verification.get("assignee", "Unknown"),
        "claimType": CLAIM_TYPE_LABELS.get(claim_type, claim_type),
        "expiry": _format_date_strict(expiry),
        "riskBand": risk_result["riskBand"],
        "reason": _build_short_reason(blocks_use, claim_type, has_continuations),
        "hasContinuations": has_continuations,
        "status": status,
    }


def _build_short_reason(
    blocks_use: Optional[bool],
    claim_type: str,
    has_continuations: bool,
) -> str:
    """Build SHORT human-readable reason (6-12 words per spec)."""
    # Short claim type explanations
    claim_reasons = {
        "COMPOSITION": "Composition claim covers API",
        "METHOD_OF_TREATMENT": "Method claim covers therapeutic use",
        "FORMULATION": "Formulation claim covers delivery",
        "PROCESS": "Process claim covers manufacturing",
        "OTHER": "Claim scope requires analysis",
    }
    
    base = claim_reasons.get(claim_type, "Claim requires analysis")
    
    if blocks_use is True:
        if has_continuations:
            return f"{base}; continuations may extend"
        return base
    elif blocks_use is False:
        return "Does not block intended use"
    else:
        return "Blocking status uncertain; review needed"


def _normalize_patent_risk(raw_score: float, blocks_use: Optional[bool], status: str) -> tuple:
    """
    DEPRECATED: Use normalize_patent_risk from normalizer.py instead.
    Kept for backwards compatibility during transition.
    """
    result = normalize_patent_risk(raw_score, blocks_use, status)
    return (result["normalizedRisk"], result["riskBand"])
def _build_source_url(patent_num: str) -> str:
    """Build Google Patents URL for patent traceability."""
    if not patent_num or patent_num == "Unknown":
        return ""
    # Clean patent number (remove spaces, ensure valid format)
    clean_num = patent_num.replace(" ", "").upper()
    return f"https://patents.google.com/patent/{clean_num}"


def _is_expired(expiry: Optional[str]) -> bool:
    """Check if patent is expired based on expiry date."""
    if not expiry:
        return False
    try:
        expiry_dt = datetime.strptime(expiry[:10], "%Y-%m-%d")
        return expiry_dt < datetime.now()
    except:
        return False


def _format_date(date_str: Optional[str]) -> str:
    """Format date string for display (legacy)."""
    if not date_str:
        return "Unknown"
    try:
        return date_str[:10]  # Return YYYY-MM-DD portion
    except:
        return "Unknown"


def _format_date_strict(date_str: Optional[str]) -> Optional[str]:
    """
    Format date string strictly to YYYY-MM-DD or return None.
    Per spec: ftoDate and expiry must be YYYY-MM-DD or null.
    """
    if not date_str:
        return None
    try:
        # Validate it's a proper date
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except:
        return None


def _build_reason(
    blocks_use: Optional[bool],
    claim_type: str,
    has_continuations: bool,
    expiry: Optional[str],
    error: Optional[str] = None,
) -> str:
    """
    Build human-readable reason for patent status with actionable context.
    NOTE: This is the LONG version for legal rationale. Use _build_short_reason for display.
    """
    if error:
        return f"Analysis error: {error}. Manual review required to assess blocking status."
    
    parts = []
    
    # Claim type explanation with business impact
    claim_explanations = {
        "COMPOSITION": "Composition claim covers the active pharmaceutical ingredient (API) - this is the strongest form of patent protection and typically cannot be designed around",
        "METHOD_OF_TREATMENT": "Method-of-treatment claim covers the therapeutic use for specific indication - may be avoided by targeting different indications",
        "FORMULATION": "Formulation claim covers specific drug delivery or dosage form - alternative formulations may provide design-around opportunities",
        "PROCESS": "Process claim covers manufacturing method - alternative synthesis routes may be viable",
        "OTHER": "Claim scope requires expert analysis to determine impact",
    }
    parts.append(claim_explanations.get(claim_type, "Claim type requires analysis"))
    
    # Blocking status with recommendation hint
    if blocks_use is True:
        parts.append("This patent blocks the intended commercial use")
    elif blocks_use is False:
        parts.append("This patent does not block the intended use based on claim analysis")
    else:
        parts.append("Blocking status could not be determined automatically - manual claim review needed")
    
    # Continuation warning with context
    if has_continuations:
        parts.append("Patent family includes continuations that may extend protection beyond listed expiry")
    
    # Near-expiry note with timeline
    if expiry:
        try:
            years = _years_until_expiry(expiry)
            if years is not None:
                if years < 1:
                    parts.append(f"Expires in less than 1 year - wait strategy highly viable")
                elif years < 3:
                    parts.append(f"Expires in {years:.1f} years - delay strategy may be cost-effective")
                elif years < 5:
                    parts.append(f"Expires in {years:.1f} years - licensing or design-around recommended")
        except:
            pass
    
    return ". ".join(parts) + "."


def _years_until_expiry(expiry: str) -> Optional[float]:
    """Calculate years until patent expiry."""
    try:
        expiry_dt = datetime.strptime(expiry[:10], "%Y-%m-%d")
        days = (expiry_dt - datetime.now()).days
        return max(0, days / 365.25)
    except:
        return None


# ============================================================================
# VISUALIZATION PAYLOAD BUILDER
# ============================================================================


def build_visualization_payload(
    verifications: List[Dict[str, Any]],
    normalized_result: Dict[str, Any],
    blocking_patents: List[Dict[str, Any]],
    non_blocking_patents: List[Dict[str, Any]],
    expired_patents: List[Dict[str, Any]],
    uncertain_patents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build structured visualization payload for frontend rendering.
    
    ═══════════════════════════════════════════════════════════════════════════
    OUTPUT SCHEMA (Jan 2026 - fixes pie legend NaN):
    ═══════════════════════════════════════════════════════════════════════════
    
    Returns:
        {
            "ftoGauge": { "value": 82, "band": "CRITICAL", "color": "#ef4444" },
            "pieData": [
                {"label": "Blocking", "count": 3},
                {"label": "Other", "count": 41}
            ],
            "blockingPatentsSummary": {
                "count": 3,
                "claimTypeCounts": {"Composition": 2, "Method of Treatment": 1}
            },
            "expiryTimeline": [ { "patent": "US...", "expiryDate": "2039-01-31" } ]
        }
    
    NOTE: pieData labels MUST be strings, counts MUST be integers (no NaN).
    ═══════════════════════════════════════════════════════════════════════════
    """
    # Use new field names from normalizer
    normalized_risk = normalized_result.get("normalizedRiskInternal", normalized_result.get("ftoIndex", 0))
    band = normalized_result.get("band", "CLEAR")
    
    # FTO Gauge data
    fto_gauge = {
        "value": int(normalized_risk) if normalized_risk is not None else 0,
        "band": band,
        "color": get_band_color(band),
        "description": get_band_description(band),
    }
    
    # =========================================================================
    # PIE DATA - Fix NaN bug by ensuring counts are always integers
    # =========================================================================
    blocking_count = len(blocking_patents) if blocking_patents else 0
    total_patents = len(verifications) if verifications else 0
    other_count = max(0, total_patents - blocking_count)  # Ensure non-negative
    
    # Ensure no NaN values - coerce to int
    blocking_count = int(blocking_count) if blocking_count == blocking_count else 0  # NaN check
    other_count = int(other_count) if other_count == other_count else 0
    
    pie_data = [
        {"label": "Blocking", "count": blocking_count},
        {"label": "Other", "count": other_count},
    ]
    
    # =========================================================================
    # BLOCKING PATENTS SUMMARY with claimTypeCounts
    # =========================================================================
    claim_type_counts = {}
    for p in (blocking_patents or []):
        ct = p.get("claimType", "OTHER")
        # Humanize claim type for display
        ct_display = CLAIM_TYPE_LABELS.get(ct, ct)
        claim_type_counts[ct_display] = claim_type_counts.get(ct_display, 0) + 1
    
    blocking_patents_summary = {
        "count": blocking_count,
        "claimTypeCounts": claim_type_counts,
    }
    
    # Expiry timeline (all patents with expiry dates)
    expiry_timeline = []
    for v in (verifications or []):
        expiry = v.get("expectedExpiry")
        if expiry:
            blocks_use = v.get("blocksUse")
            status = "Blocking" if blocks_use is True else "Non-blocking"
            if _is_expired(expiry):
                status = "Expired"
            expiry_timeline.append({
                "patentNumber": v.get("patent", "Unknown"),
                "expiryDate": _format_date_strict(expiry),
                "status": status,
                "claimType": CLAIM_TYPE_LABELS.get(v.get("claimType", "OTHER"), "Other"),
            })
    
    # Sort by expiry date
    expiry_timeline.sort(key=lambda x: x.get("expiryDate") or "9999-12-31")
    
    # Legacy counts (kept for backward compatibility)
    counts = {
        "blocking": blocking_count,
        "nonBlocking": len(non_blocking_patents) if non_blocking_patents else 0,
        "expired": len(expired_patents) if expired_patents else 0,
        "uncertain": len(uncertain_patents) if uncertain_patents else 0,
    }
    
    return {
        "ftoGauge": fto_gauge,
        "pieData": pie_data,
        "blockingPatentsSummary": blocking_patents_summary,
        "expiryTimeline": expiry_timeline,
        "counts": counts,  # Legacy field
    }


# ============================================================================
# SUMMARY TEXT BUILDERS
# ============================================================================


def build_summary_texts(
    verifications: List[Dict[str, Any]],
    normalized_result: Dict[str, Any],
    drug: str,
    disease: str,
    blocking_patents: List[Dict[str, Any]],
    earliest_freedom_date: Optional[str],
    recommended_actions: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Build multi-layer summary texts for different audiences.
    
    Returns:
        {
            "executive": "1-2 sentence C-suite summary",
            "business": "3-6 line business interpretation",
            "legal": "Detailed legal rationale (expandable)"
        }
    """
    # Use new field names
    normalized_risk = normalized_result.get("normalizedRiskInternal", normalized_result.get("ftoIndex", 0))
    band = normalized_result.get("band", "CLEAR")
    num_blocking = len(blocking_patents) if blocking_patents else 0
    
    # Build executive summary (1-2 sentences)
    executive = _build_executive_summary(
        drug, disease, normalized_risk, band, num_blocking, earliest_freedom_date
    )
    
    # Build business summary (3-6 lines)
    business = _build_business_summary(
        drug, disease, normalized_risk, band, blocking_patents, 
        earliest_freedom_date, recommended_actions
    )
    
    # Build legal rationale (expandable)
    legal = _build_legal_rationale(
        drug, disease, blocking_patents, verifications
    )
    
    return {
        "executive": executive,
        "business": business,
        "legal": legal,
    }


def _build_executive_summary(
    drug: str,
    disease: str,
    normalized_risk: int,
    band: str,
    num_blocking: int,
    earliest_freedom_date: Optional[str],
) -> str:
    """Build 1-2 sentence executive summary."""
    if band == "CLEAR":
        return f"FTO assessment for {drug} in {disease}: CLEAR. No blocking patents identified. Recommend standard IP monitoring."
    
    elif band == "LOW":
        return f"FTO assessment for {drug} in {disease}: LOW RISK. Minor patent concerns identified. Proceed with caution and monitor landscape."
    
    elif band == "MODERATE":
        return f"FTO assessment for {drug} in {disease}: MODERATE RISK (Index: {normalized_risk}/100). {num_blocking} blocking patent(s) require attention. Recommend patent counsel review before proceeding."
    
    elif band == "HIGH":
        freedom_note = f" Earliest FTO date: {earliest_freedom_date}." if earliest_freedom_date else ""
        return f"FTO assessment for {drug} in {disease}: HIGH RISK (Index: {normalized_risk}/100). {num_blocking} blocking patent(s) create significant barriers.{freedom_note} Licensing negotiations recommended."
    
    else:  # CRITICAL
        freedom_note = f" Earliest FTO date: {earliest_freedom_date}." if earliest_freedom_date else ""
        return f"CRITICAL FTO RISK for {drug} in {disease} (Index: {normalized_risk}/100). {num_blocking} blocking patent(s) prevent commercialization.{freedom_note} Licensing required before proceeding."


def _build_business_summary(
    drug: str,
    disease: str,
    normalized_risk: int,
    band: str,
    blocking_patents: List[Dict[str, Any]],
    earliest_freedom_date: Optional[str],
    recommended_actions: List[Dict[str, Any]],
) -> str:
    """Build 3-6 line business interpretation."""
    lines = []
    
    # Opening assessment
    lines.append(f"Freedom-to-Operate assessment for {drug} in {disease} indicates {band} risk (Index: {normalized_risk}/100).")
    
    if not blocking_patents:
        lines.append("No blocking patents identified in USPTO search.")
        lines.append("Recommended: Proceed with development while maintaining IP monitoring.")
        return " ".join(lines)
    
    # Blocking patent impact
    composition_blockers = [p for p in blocking_patents if p.get("claimType") == "COMPOSITION"]
    method_blockers = [p for p in blocking_patents if p.get("claimType") == "METHOD_OF_TREATMENT"]
    
    if composition_blockers:
        lines.append(f"{len(composition_blockers)} composition patent(s) directly cover the API, making design-around difficult.")
    
    if method_blockers:
        lines.append(f"{len(method_blockers)} method-of-treatment patent(s) cover the therapeutic indication.")
    
    # Timeline impact - use ftoDate terminology
    if earliest_freedom_date:
        lines.append(f"Earliest FTO date: {earliest_freedom_date}.")
    
    # Options summary
    if recommended_actions:
        top_actions = recommended_actions[:2]
        action_summary = ", ".join([a.get("action", "") for a in top_actions if a.get("action")])
        if action_summary:
            lines.append(f"Primary options: {action_summary}.")
    
    # Trade-offs
    if band in ("HIGH", "CRITICAL"):
        lines.append("Trade-offs: Licensing provides fastest path to market but increases costs. Waiting for expiry delays launch significantly.")
    
    return " ".join(lines)


def _build_legal_rationale(
    drug: str,
    disease: str,
    blocking_patents: List[Dict[str, Any]],
    verifications: List[Dict[str, Any]],
) -> str:
    """Build detailed legal rationale (expandable section)."""
    lines = []
    
    lines.append(f"FTO Legal Analysis: {drug} for {disease}")
    lines.append("")
    
    if not blocking_patents:
        lines.append("No blocking patents identified. However, recommend:")
        lines.append("• Manual review of related patent families")
        lines.append("• Monitor continuation applications")
        lines.append("• Review international patent landscape")
        return "\n".join(lines)
    
    lines.append("BLOCKING PATENT ANALYSIS:")
    lines.append("")
    
    for i, p in enumerate(blocking_patents[:5], 1):
        patent_num = p.get("patent", "Unknown")
        claim_type = p.get("claimType", "OTHER")
        expiry = p.get("expectedExpiry", "Unknown")
        confidence = p.get("confidence", "LOW")
        
        lines.append(f"{i}. {patent_num}")
        lines.append(f"   • Claim Type: {CLAIM_TYPE_LABELS.get(claim_type, claim_type)}")
        lines.append(f"   • Expected Expiry: {expiry}")
        lines.append(f"   • Analysis Confidence: {confidence}")
        
        if p.get("hasContinuations"):
            lines.append("   • WARNING: Continuation applications may extend protection")
        
        lines.append("")
    
    lines.append("RECOMMENDED FOCUS FOR COUNSEL:")
    lines.append("• Detailed claim charting against proposed product")
    lines.append("• Review prosecution history for claim scope limitations")
    lines.append("• Assess validity challenges (prior art search)")
    lines.append("• Evaluate continuation application status")
    lines.append("")
    lines.append("INFORMATION GAPS:")
    lines.append("• Full claim text not analyzed (automated summary only)")
    lines.append("• Prosecution history estoppel not evaluated")
    lines.append("• Related foreign patents not searched")
    
    return "\n".join(lines)


__all__ = [
    "humanize_field_name",
    "format_patent_entry",
    "build_visualization_payload",
    "build_summary_texts",
]
