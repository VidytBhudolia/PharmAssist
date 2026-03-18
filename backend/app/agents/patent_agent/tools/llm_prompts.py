"""
LLM Prompt Templates for FTO Summary Generation

IMPORTANT: LLM is used ONLY for narrative text generation, NOT for decisions or scoring.
All FTO decisions are deterministic and rule-based.

These prompts generate human-readable summaries for different audiences:
- Executive: C-suite, 1-2 sentences
- Business: Commercial/strategy teams, 3-6 lines
- Legal: Patent practitioners, expandable detail
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

EXECUTIVE_PROMPT_TEMPLATE = """You are an expert product-facing summarizer. Given the following FTO analysis data, generate a 1-2 sentence executive summary suitable for C-suite executives.

FTO Analysis Data:
- Drug: {drug}
- Disease/Indication: {disease}
- FTO Risk Index: {fto_index}/100
- Risk Band: {band}
- Blocking Patents: {blocking_count}
- Earliest Freedom Date: {earliest_freedom_date}
- Top Blocking Patents: {top_blocking}

RULES:
- State the recommendation in plain language
- Include one-sentence rationale
- End with one-line recommended next step
- Do NOT give legal advice
- Keep to 1-2 sentences maximum

Generate the executive summary:"""


BUSINESS_PROMPT_TEMPLATE = """You are a pharmaceutical business analyst. Using the FTO analysis data below, produce a 3-6 line business interpretation.

FTO Analysis Data:
- Drug: {drug}
- Disease/Indication: {disease}
- FTO Risk Index: {fto_index}/100
- Risk Band: {band}
- Blocking Patents: {blocking_count}
- Composition Blockers: {composition_count}
- Method Blockers: {method_count}
- Earliest Freedom Date: {earliest_freedom_date}
- Recommended Actions: {actions}

Include:
1. Expected commercial impacts
2. Time-to-market blockers
3. 1-2 practical choices (license vs. delay vs. design-around)
4. Trade-offs for each choice
5. One immediate action item for each choice

RULES:
- Use plain business language
- Focus on commercial implications
- Do NOT give legal advice
- Keep to 3-6 lines

Generate the business summary:"""


LEGAL_PROMPT_TEMPLATE = """You are a patent practitioner drafting an FTO analysis summary. Using the data below, produce a 6-10 line legal rationale.

FTO Analysis Data:
- Drug: {drug}
- Disease/Indication: {disease}
- FTO Risk Index: {fto_index}/100
- Risk Band: {band}
- Jurisdiction: {jurisdiction}

Blocking Patents Analysis:
{patent_details}

Include:
1. Why the identified patents are blocking (claim scope)
2. What a formal FTO opinion would focus on
3. Claim chart targets for key patents
4. Final bullet: "Information missing / next docs to fetch"

RULES:
- Use objective, plain language
- Assume reader is a patent practitioner
- Do NOT make definitive legal conclusions
- Highlight areas requiring further investigation

Generate the legal rationale:"""


# ============================================================================
# PROMPT BUILDER FUNCTIONS
# ============================================================================


def build_executive_prompt(
    drug: str,
    disease: str,
    fto_index: int,
    band: str,
    blocking_count: int,
    earliest_freedom_date: Optional[str],
    top_blocking_patents: List[Dict[str, Any]],
) -> str:
    """
    Build the executive summary prompt with structured input data.
    
    Args:
        drug: Target drug name
        disease: Target disease/indication
        fto_index: Normalized FTO risk index (0-100)
        band: Risk band (LOW/MODERATE/HIGH/CRITICAL)
        blocking_count: Number of blocking patents
        earliest_freedom_date: When all blocking patents expire (or None)
        top_blocking_patents: Top 2 blocking patents for context
    
    Returns:
        Formatted prompt string ready for LLM call
    """
    # Format top blocking patents
    top_blocking_str = "None identified"
    if top_blocking_patents:
        top_2 = top_blocking_patents[:2]
        top_blocking_str = "; ".join([
            f"{p.get('patent', 'Unknown')} ({p.get('claimType', 'OTHER')}, expires {p.get('expectedExpiry', 'unknown')[:10] if p.get('expectedExpiry') else 'unknown'})"
            for p in top_2
        ])
    
    return EXECUTIVE_PROMPT_TEMPLATE.format(
        drug=drug,
        disease=disease,
        fto_index=fto_index,
        band=band,
        blocking_count=blocking_count,
        earliest_freedom_date=earliest_freedom_date or "N/A",
        top_blocking=top_blocking_str,
    )


def build_business_prompt(
    drug: str,
    disease: str,
    fto_index: int,
    band: str,
    blocking_patents: List[Dict[str, Any]],
    earliest_freedom_date: Optional[str],
    recommended_actions: List[Dict[str, Any]],
) -> str:
    """
    Build the business summary prompt with structured input data.
    
    Args:
        drug: Target drug name
        disease: Target disease/indication
        fto_index: Normalized FTO risk index (0-100)
        band: Risk band
        blocking_patents: List of blocking patents
        earliest_freedom_date: When all blocking patents expire
        recommended_actions: List of recommended actions
    
    Returns:
        Formatted prompt string ready for LLM call
    """
    # Count by claim type
    composition_count = sum(1 for p in blocking_patents if p.get("claimType") == "COMPOSITION")
    method_count = sum(1 for p in blocking_patents if p.get("claimType") == "METHOD_OF_TREATMENT")
    
    # Format actions
    actions_str = ", ".join([a.get("action", "") for a in recommended_actions[:3]])
    
    return BUSINESS_PROMPT_TEMPLATE.format(
        drug=drug,
        disease=disease,
        fto_index=fto_index,
        band=band,
        blocking_count=len(blocking_patents),
        composition_count=composition_count,
        method_count=method_count,
        earliest_freedom_date=earliest_freedom_date or "N/A",
        actions=actions_str or "To be determined",
    )


def build_legal_prompt(
    drug: str,
    disease: str,
    fto_index: int,
    band: str,
    jurisdiction: str,
    blocking_patents: List[Dict[str, Any]],
) -> str:
    """
    Build the legal rationale prompt with structured input data.
    
    Args:
        drug: Target drug name
        disease: Target disease/indication
        fto_index: Normalized FTO risk index (0-100)
        band: Risk band
        jurisdiction: Patent jurisdiction
        blocking_patents: List of blocking patents with details
    
    Returns:
        Formatted prompt string ready for LLM call
    """
    # Format patent details
    patent_lines = []
    for i, p in enumerate(blocking_patents[:5], 1):
        patent_lines.append(
            f"{i}. {p.get('patent', 'Unknown')}: "
            f"{p.get('claimType', 'OTHER')} claim, "
            f"expires {p.get('expectedExpiry', 'unknown')[:10] if p.get('expectedExpiry') else 'unknown'}, "
            f"confidence {p.get('confidence', 'LOW')}"
            f"{', has continuations' if p.get('hasContinuations') else ''}"
        )
    
    patent_details = "\n".join(patent_lines) if patent_lines else "No blocking patents identified"
    
    return LEGAL_PROMPT_TEMPLATE.format(
        drug=drug,
        disease=disease,
        fto_index=fto_index,
        band=band,
        jurisdiction=jurisdiction,
        patent_details=patent_details,
    )


# ============================================================================
# FALLBACK SUMMARIES (when LLM unavailable)
# ============================================================================


def generate_fallback_executive(
    drug: str,
    disease: str,
    fto_index: int,
    band: str,
    blocking_count: int,
    earliest_freedom_date: Optional[str],
) -> str:
    """Generate deterministic executive summary when LLM unavailable."""
    if band == "LOW":
        return f"FTO assessment for {drug} in {disease}: LOW RISK. No significant patent barriers. Proceed with standard IP monitoring."
    
    elif band == "MODERATE":
        return f"FTO assessment for {drug} in {disease}: MODERATE RISK (Index: {fto_index}/100). {blocking_count} blocking patent(s) identified. Recommend patent counsel review."
    
    elif band == "HIGH":
        freedom = f" Earliest freedom: {earliest_freedom_date}." if earliest_freedom_date else ""
        return f"HIGH RISK FTO for {drug} in {disease} (Index: {fto_index}/100). {blocking_count} blocking patent(s).{freedom} Licensing recommended."
    
    else:  # CRITICAL
        freedom = f" Freedom date: {earliest_freedom_date}." if earliest_freedom_date else ""
        return f"CRITICAL FTO RISK for {drug} in {disease} (Index: {fto_index}/100). {blocking_count} severe blocking patent(s).{freedom} Licensing required."


def generate_fallback_business(
    drug: str,
    disease: str,
    fto_index: int,
    band: str,
    blocking_patents: List[Dict[str, Any]],
    earliest_freedom_date: Optional[str],
) -> str:
    """Generate deterministic business summary when LLM unavailable."""
    lines = [f"FTO assessment for {drug} in {disease}: {band} risk (Index: {fto_index}/100)."]
    
    if not blocking_patents:
        lines.append("No blocking patents identified. Proceed with development and standard IP monitoring.")
        return " ".join(lines)
    
    composition_count = sum(1 for p in blocking_patents if p.get("claimType") == "COMPOSITION")
    if composition_count:
        lines.append(f"{composition_count} composition patent(s) block the API directly.")
    
    if earliest_freedom_date:
        lines.append(f"Earliest freedom date: {earliest_freedom_date}.")
    
    if band in ("HIGH", "CRITICAL"):
        lines.append("Options: (1) License - fastest but costly, (2) Wait for expiry - delays launch.")
    else:
        lines.append("Options: (1) Proceed with caution, (2) Seek FTO opinion from counsel.")
    
    return " ".join(lines)


def generate_fallback_legal(
    drug: str,
    disease: str,
    blocking_patents: List[Dict[str, Any]],
) -> str:
    """Generate deterministic legal rationale when LLM unavailable."""
    lines = [f"FTO Legal Analysis: {drug} for {disease}", ""]
    
    if not blocking_patents:
        lines.append("No blocking patents identified in automated search.")
        lines.append("")
        lines.append("RECOMMENDED ACTIONS:")
        lines.append("• Manual review of related patent families")
        lines.append("• Monitor continuation applications")
        lines.append("• Review international patent landscape")
        return "\n".join(lines)
    
    lines.append("BLOCKING PATENTS:")
    for i, p in enumerate(blocking_patents[:5], 1):
        lines.append(f"{i}. {p.get('patent', 'Unknown')} - {p.get('claimType', 'OTHER')} claim, expires {p.get('expectedExpiry', 'unknown')[:10] if p.get('expectedExpiry') else 'unknown'}")
    
    lines.append("")
    lines.append("COUNSEL FOCUS AREAS:")
    lines.append("• Claim charting against proposed product")
    lines.append("• Prosecution history review")
    lines.append("• Validity assessment (prior art)")
    lines.append("")
    lines.append("INFORMATION GAPS:")
    lines.append("• Full claim text (automated summary only)")
    lines.append("• Prosecution history estoppel")
    lines.append("• Foreign patent coverage")
    
    return "\n".join(lines)


__all__ = [
    "EXECUTIVE_PROMPT_TEMPLATE",
    "BUSINESS_PROMPT_TEMPLATE",
    "LEGAL_PROMPT_TEMPLATE",
    "build_executive_prompt",
    "build_business_prompt",
    "build_legal_prompt",
    "generate_fallback_executive",
    "generate_fallback_business",
    "generate_fallback_legal",
]
