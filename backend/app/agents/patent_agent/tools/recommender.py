"""
FTO Recommendation Engine

Generates actionable, feasibility-rated recommendations based on FTO analysis.
Returns TOP 3 most relevant recommendations, each with a single nextStep.

RECOMMENDATION RULES:
- Composition blocking → License (HIGH), Design-around (LOW)
- Method near expiry (<5y) → Wait/Monitor (HIGH), File improvements (MEDIUM)
- Multiple uncertain → Manual review (HIGH)
- HIGH/CRITICAL band → Always add "Engage patent counsel immediately"

OUTPUT FORMAT:
Each recommendation contains:
- action: Short action name (string)
- reason: One-sentence reason tied to patents/claims (6-12 words)
- feasibility: "HIGH" | "MEDIUM" | "LOW"
- nextStep: Single short sentence for next action
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================================
# RECOMMENDATION TEMPLATES
# ============================================================================

RECOMMENDATION_TEMPLATES = {
    "license": {
        "action": "License",
        "reason_template": "Composition claims block API; licensing fastest path forward",
        "feasibility": "HIGH",
        "nextStep": "Contact patent counsel to assess licensing options",
        "priority": 1,  # Higher = more important
    },
    "engage_counsel": {
        "action": "Engage Patent Counsel",
        "reason_template": "Risk level requires immediate professional legal guidance",
        "feasibility": "HIGH",
        "nextStep": "Contact IP/patent counsel within 48 hours",
        "priority": 2,
    },
    "design_around": {
        "action": "Design-Around",
        "reason_template": "Modify formulation or delivery to avoid claim coverage",
        "feasibility": "LOW",
        "nextStep": "Consult R&D on alternative formulation strategies",
        "priority": 3,
    },
    "wait_monitor": {
        "action": "Wait / Monitor",
        "reason_template": "Blocking patents expire soon; delay may be cost-effective",
        "feasibility": "HIGH",
        "nextStep": "Monitor patent status and continuation filings",
        "priority": 4,
    },
    "indication_shift": {
        "action": "Indication Shift",
        "reason_template": "Alternative indication may avoid method claim coverage",
        "feasibility": "MEDIUM",
        "nextStep": "Review clinical data for off-label uses",
        "priority": 5,
    },
    "file_improvements": {
        "action": "File Improvement Patents",
        "reason_template": "Secure IP position for formulation improvements",
        "feasibility": "MEDIUM",
        "nextStep": "Identify patentable formulation or delivery improvements",
        "priority": 6,
    },
    "manual_review": {
        "action": "Manual Review Required",
        "reason_template": "Multiple patents with uncertain status need expert analysis",
        "feasibility": "HIGH",
        "nextStep": "Engage patent counsel for detailed claim analysis",
        "priority": 7,
    },
    "proceed_clear": {
        "action": "Proceed with Standard Monitoring",
        "reason_template": "No significant blocking patents; maintain IP vigilance",
        "feasibility": "HIGH",
        "nextStep": "Set up patent monitoring alerts for drug and indication",
        "priority": 8,
    },
}


# ============================================================================
# MAIN RECOMMENDATION FUNCTION
# ============================================================================


def recommend_actions(
    verifications: List[Dict[str, Any]],
    fto_index: int,
    band: str,
    blocking_patents: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate TOP 3 actionable recommendations based on FTO analysis.
    
    Args:
        verifications: All patent verifications from analysis
        fto_index: Normalized FTO risk index (0-100)
        band: Risk band ("CLEAR", "LOW", "MODERATE", "HIGH", "CRITICAL")
        blocking_patents: List of blocking patents with details
    
    Returns:
        List of 3 recommendation dicts (sorted by priority), each containing:
        - action: Short action name
        - reason: One-sentence reason tied to patents/claims (6-12 words)
        - feasibility: HIGH / MEDIUM / LOW
        - nextStep: Single short sentence for next action
    """
    if blocking_patents is None:
        blocking_patents = []
    
    candidates = []  # List of (priority, recommendation_dict)
    
    # Analyze patent characteristics
    composition_blockers = [p for p in blocking_patents if p.get("claimType") == "COMPOSITION"]
    method_blockers = [p for p in blocking_patents if p.get("claimType") == "METHOD_OF_TREATMENT"]
    formulation_blockers = [p for p in blocking_patents if p.get("claimType") == "FORMULATION"]
    
    # Count uncertain patents
    uncertain_count = sum(1 for v in verifications if v.get("blocksUse") is None and not v.get("error"))
    error_count = sum(1 for v in verifications if v.get("error"))
    
    # Find near-expiry blocking patents
    near_expiry_blockers = _get_near_expiry_patents(blocking_patents, years_threshold=5)
    
    # =========================================================================
    # RULE 1: CLEAR/LOW risk band - proceed with monitoring
    # =========================================================================
    if band in ("CLEAR", "LOW"):
        rec = _build_recommendation("proceed_clear")
        candidates.append((RECOMMENDATION_TEMPLATES["proceed_clear"]["priority"], rec))
    
    # =========================================================================
    # RULE 2: HIGH/CRITICAL band → Always add "Engage patent counsel"
    # =========================================================================
    if band in ("HIGH", "CRITICAL"):
        rec = _build_recommendation("engage_counsel")
        rec["reason"] = f"FTO Risk Index {fto_index}/100 ({band}) requires legal guidance"
        candidates.append((RECOMMENDATION_TEMPLATES["engage_counsel"]["priority"], rec))
    
    # =========================================================================
    # RULE 3: COMPOSITION blocking patents → License
    # =========================================================================
    if composition_blockers:
        rec = _build_recommendation("license")
        rec["reason"] = f"{len(composition_blockers)} composition patent(s) block API; licensing required"
        candidates.append((RECOMMENDATION_TEMPLATES["license"]["priority"], rec))
        
        # Design-around is LOW feasibility for composition
        design_rec = _build_recommendation("design_around")
        design_rec["reason"] = "Composition claims difficult to design around"
        design_rec["feasibility"] = "LOW"
        candidates.append((RECOMMENDATION_TEMPLATES["design_around"]["priority"], design_rec))
    
    # =========================================================================
    # RULE 4: METHOD_OF_TREATMENT near expiry → Wait/Monitor
    # =========================================================================
    method_near_expiry = [p for p in near_expiry_blockers if p.get("claimType") == "METHOD_OF_TREATMENT"]
    if method_near_expiry:
        years = _min_years_to_expiry(method_near_expiry)
        rec = _build_recommendation("wait_monitor")
        rec["reason"] = f"Method patents expire in {years:.1f} years; delay cost-effective"
        candidates.append((RECOMMENDATION_TEMPLATES["wait_monitor"]["priority"], rec))
    
    # =========================================================================
    # RULE 5: FORMULATION blockers without composition → Design-around viable
    # =========================================================================
    if formulation_blockers and not composition_blockers:
        rec = _build_recommendation("design_around")
        rec["reason"] = "Formulation claims may be designable around"
        rec["feasibility"] = "MEDIUM"
        candidates.append((RECOMMENDATION_TEMPLATES["design_around"]["priority"], rec))
    
    # =========================================================================
    # RULE 6: Multiple uncertain patents → Manual review required
    # =========================================================================
    if uncertain_count >= 2 or error_count >= 1:
        rec = _build_recommendation("manual_review")
        rec["reason"] = f"{uncertain_count} uncertain patents require expert review"
        candidates.append((RECOMMENDATION_TEMPLATES["manual_review"]["priority"], rec))
    
    # =========================================================================
    # RULE 7: Indication shift option for method claims (no composition)
    # =========================================================================
    if method_blockers and not composition_blockers:
        rec = _build_recommendation("indication_shift")
        rec["reason"] = "Method claims indication-specific; alternative may avoid"
        candidates.append((RECOMMENDATION_TEMPLATES["indication_shift"]["priority"], rec))
    
    # =========================================================================
    # RULE 8: MODERATE band - add file improvements
    # =========================================================================
    if band == "MODERATE" and blocking_patents:
        rec = _build_recommendation("file_improvements")
        rec["reason"] = "Secure IP position for formulation improvements"
        candidates.append((RECOMMENDATION_TEMPLATES["file_improvements"]["priority"], rec))
    
    # Deduplicate by action name, keeping highest priority (lowest number)
    seen_actions = {}
    for priority, rec in candidates:
        action = rec["action"]
        if action not in seen_actions or priority < seen_actions[action][0]:
            seen_actions[action] = (priority, rec)
    
    # Sort by priority (lower number = higher priority) and take top 3
    sorted_recs = sorted(seen_actions.values(), key=lambda x: x[0])
    top_3 = [rec for _, rec in sorted_recs[:3]]
    
    # Ensure we have at least 1 recommendation (fallback)
    if not top_3:
        top_3.append(_build_recommendation("proceed_clear"))
    
    return top_3


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _build_recommendation(template_key: str) -> Dict[str, Any]:
    """Build a recommendation dict from a template.
    
    Returns:
        Dict with: action, reason, feasibility, nextStep
    """
    template = RECOMMENDATION_TEMPLATES.get(template_key, {})
    return {
        "action": template.get("action", "Unknown Action"),
        "reason": template.get("reason_template", ""),
        "feasibility": template.get("feasibility", "MEDIUM"),
        "nextStep": template.get("nextStep", "Consult with IP counsel"),
    }


def _get_near_expiry_patents(patents: List[Dict[str, Any]], years_threshold: float = 5) -> List[Dict[str, Any]]:
    """Get patents expiring within threshold years."""
    near_expiry = []
    for p in patents:
        expiry = p.get("expectedExpiry") or p.get("expiry")
        if expiry:
            years = _years_until_expiry(expiry)
            if years is not None and years < years_threshold:
                near_expiry.append(p)
    return near_expiry


def _years_until_expiry(expiry: str) -> Optional[float]:
    """Calculate years until patent expiry."""
    try:
        expiry_dt = datetime.strptime(expiry[:10], "%Y-%m-%d")
        days = (expiry_dt - datetime.now()).days
        return max(0, days / 365.25)
    except:
        return None


def _min_years_to_expiry(patents: List[Dict[str, Any]]) -> float:
    """Get minimum years to expiry among patents."""
    min_years = float("inf")
    for p in patents:
        expiry = p.get("expectedExpiry") or p.get("expiry")
        if expiry:
            years = _years_until_expiry(expiry)
            if years is not None and years < min_years:
                min_years = years
    return min_years if min_years != float("inf") else 0


__all__ = ["recommend_actions"]
