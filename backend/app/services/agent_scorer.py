"""
Agent Feasibility Scoring Engine
=================================
Each agent computes a **feasibility score** from 1-100 (0 = critical blocker).

Score semantics
---------------
  0       : Critical blocker (e.g. blocking patent, import ban)
  1 – 20  : Very unfavourable — major barriers
 21 – 40  : Unfavourable — significant risks
 41 – 60  : Neutral / mixed signals
 61 – 80  : Favourable — encouraging evidence
 81 – 100 : Highly favourable — strong green signal

The score is injected into every agent's ``summary`` / ``bannerSummary``
dict under the key ``"feasibilityScore"`` so the frontend can render it
alongside the existing banner.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


# ── helpers ──────────────────────────────────────────────────────────────────
def _clamp(value: float, lo: float = 1.0, hi: float = 100.0) -> int:
    """Clamp and round to nearest int within [lo, hi]."""
    return int(max(lo, min(hi, round(value))))


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ═════════════════════════════════════════════════════════════════════════════
#  Per-agent scoring functions
# ═════════════════════════════════════════════════════════════════════════════

def score_iqvia(
    *,
    market_size_usd: Optional[float] = None,
    cagr_percent: Optional[float] = None,
    total_growth_percent: Optional[float] = None,
    num_competitors: int = 0,
    leader_share_value: Optional[float] = None,
    has_articles: bool = False,
    using_mock_data: bool = False,
) -> Dict[str, Any]:
    """Score IQVIA market feasibility.

    Factors (weighted):
        - Market size        30 pts  (larger = better opportunity)
        - CAGR / growth      35 pts  (higher growth = better)
        - Competition level  20 pts  (moderate competition = good;
                                       too concentrated = bad)
        - Data quality       15 pts  (real data, articles available)
    """
    pts = 0.0

    # ── Market size (30 pts) ──
    ms = _safe_float(market_size_usd)
    if ms >= 50:
        pts += 30
    elif ms >= 20:
        pts += 25
    elif ms >= 10:
        pts += 20
    elif ms >= 5:
        pts += 15
    elif ms >= 1:
        pts += 10
    elif ms > 0:
        pts += 5

    # ── CAGR (35 pts) ──
    cagr = _safe_float(cagr_percent)
    if cagr > 15:
        pts += 35
    elif cagr > 10:
        pts += 30
    elif cagr > 7:
        pts += 25
    elif cagr > 5:
        pts += 20
    elif cagr > 3:
        pts += 14
    elif cagr > 0:
        pts += 8
    elif cagr < -3:
        pts += 0  # declining
    elif cagr < 0:
        pts += 3

    # ── Competition landscape (20 pts) ──
    lsv = _safe_float(leader_share_value)
    if lsv > 70:
        # One player dominates — hard to break in
        pts += 5
    elif lsv > 50:
        pts += 10
    elif lsv > 30:
        # Healthy competition: room for new entrants
        pts += 18
    elif num_competitors >= 3:
        pts += 20  # fragmented
    elif num_competitors > 0:
        pts += 15
    else:
        pts += 10  # unknown competition

    # ── Data quality (15 pts) ──
    if not using_mock_data:
        pts += 10
    else:
        pts += 4  # some credit for illustrative data
    if has_articles:
        pts += 5

    score = _clamp(pts)

    reason = _label(score)
    return {"score": score, "label": reason}


def score_patent(
    *,
    fto_status: Optional[str] = None,
    blocking_count: int = 0,
    fto_date: Optional[str] = None,
    normalized_risk: Optional[float] = None,
    total_patents: int = 0,
) -> Dict[str, Any]:
    """Score patent feasibility (freedom-to-operate perspective).

    A **0** is returned for BLOCKED status — this is a critical blocker.
    """
    status = (fto_status or "").upper()

    if status == "BLOCKED":
        return {"score": 0, "label": "Critical Blocker", "isCritical": True,
                "criticalReason": f"Patent BLOCKED — {blocking_count} blocking patent(s) found"}

    if status == "CLEAR":
        base = 90
    elif status == "NEEDS_MONITORING":
        base = 60
    elif status == "AT_RISK":
        base = 30
    else:
        base = 50  # unknown

    # Adjust for blocking count
    if blocking_count == 0:
        base = min(base + 10, 100)
    elif blocking_count <= 2:
        base = max(base - 10, 1)
    else:
        base = max(base - 20, 1)

    # Adjust for FTO date proximity
    if fto_date:
        try:
            import datetime
            fto_dt = datetime.datetime.strptime(fto_date[:10], "%Y-%m-%d")
            years_away = (fto_dt - datetime.datetime.utcnow()).days / 365.25
            if years_away <= 0:
                base = min(base + 10, 100)  # already expired
            elif years_away <= 2:
                base = min(base + 5, 100)   # expiring soon
            elif years_away > 10:
                base = max(base - 5, 1)     # far away
        except (ValueError, TypeError):
            pass

    score = _clamp(base)
    return {"score": score, "label": _label(score)}


def score_clinical(
    *,
    total_trials: int = 0,
    phase_counts: Optional[Dict[str, int]] = None,
    top_sponsors_count: int = 0,
) -> Dict[str, Any]:
    """Score clinical evidence strength.

    Factors:
        - Trial volume        30 pts
        - Phase maturity      50 pts  (Phase III/IV = mature)
        - Sponsor breadth     20 pts  (multiple sponsors = validated)
    """
    pc = phase_counts or {}
    pts = 0.0

    # ── Trial volume (30 pts) ──
    if total_trials >= 20:
        pts += 30
    elif total_trials >= 10:
        pts += 25
    elif total_trials >= 5:
        pts += 18
    elif total_trials >= 2:
        pts += 12
    elif total_trials == 1:
        pts += 6
    # 0 trials = 0 pts

    # ── Phase maturity (50 pts) ──
    p4 = pc.get("Phase 4", 0) + pc.get("PHASE4", 0) + pc.get("Phase IV", 0)
    p3 = pc.get("Phase 3", 0) + pc.get("PHASE3", 0) + pc.get("Phase III", 0)
    p2 = pc.get("Phase 2", 0) + pc.get("PHASE2", 0) + pc.get("Phase II", 0)
    p1 = pc.get("Phase 1", 0) + pc.get("PHASE1", 0) + pc.get("Phase I", 0)

    if p4 > 0:
        pts += 50
    elif p3 >= 3:
        pts += 45
    elif p3 >= 1:
        pts += 35
    elif p2 >= 3:
        pts += 25
    elif p2 >= 1:
        pts += 18
    elif p1 >= 1:
        pts += 10

    # ── Sponsor breadth (20 pts) ──
    if top_sponsors_count >= 5:
        pts += 20
    elif top_sponsors_count >= 3:
        pts += 15
    elif top_sponsors_count >= 1:
        pts += 8

    if total_trials == 0:
        # No clinical evidence at all — very low but not "critical blocker"
        score = 5
    else:
        score = _clamp(pts)

    return {"score": score, "label": _label(score)}


def score_exim(
    *,
    total_value_usd_million: Optional[float] = None,
    yoy_growth_percent: Optional[float] = None,
    top_partners_count: int = 0,
    trade_type: str = "export",
    has_restrictions: bool = False,
) -> Dict[str, Any]:
    """Score EXIM supply-chain feasibility.

    A **0** is returned if hard import restrictions are detected.
    """
    if has_restrictions:
        return {"score": 0, "label": "Critical Blocker", "isCritical": True,
                "criticalReason": "Active import/export restrictions detected for this product"}

    pts = 0.0
    tv = _safe_float(total_value_usd_million)
    yoy = _safe_float(yoy_growth_percent)

    # ── Trade value (40 pts) ──
    if tv >= 1000:
        pts += 40
    elif tv >= 500:
        pts += 33
    elif tv >= 100:
        pts += 25
    elif tv >= 10:
        pts += 15
    elif tv > 0:
        pts += 8

    # ── Growth (35 pts) ──
    if yoy > 20:
        pts += 35
    elif yoy > 10:
        pts += 28
    elif yoy > 5:
        pts += 22
    elif yoy > 0:
        pts += 14
    elif yoy > -5:
        pts += 8
    else:
        pts += 2  # declining

    # ── Trade diversity (25 pts) ──
    if top_partners_count >= 10:
        pts += 25
    elif top_partners_count >= 5:
        pts += 20
    elif top_partners_count >= 3:
        pts += 14
    elif top_partners_count >= 1:
        pts += 8

    score = _clamp(pts) if tv > 0 or top_partners_count > 0 else _clamp(15)
    return {"score": score, "label": _label(score)}


def score_web_intelligence(
    *,
    positive_pct: float = 0.0,
    negative_pct: float = 0.0,
    neutral_pct: float = 0.0,
    news_count: int = 0,
    forum_count: int = 0,
    signal_score: Optional[float] = None,
    has_critical_alert: bool = False,
) -> Dict[str, Any]:
    """Score web intelligence / market sentiment.

    A **0** is returned if there's a critical regulatory alert.
    """
    if has_critical_alert:
        return {"score": 0, "label": "Critical Blocker", "isCritical": True,
                "criticalReason": "Critical regulatory or safety alert detected in market intelligence"}

    pts = 0.0

    # ── Sentiment balance (50 pts) ──
    pos = _safe_float(positive_pct)
    neg = _safe_float(negative_pct)
    net = pos - neg
    if net >= 50:
        pts += 50
    elif net >= 30:
        pts += 40
    elif net >= 10:
        pts += 30
    elif net >= 0:
        pts += 20
    elif net >= -20:
        pts += 10
    else:
        pts += 3

    # ── Coverage breadth (30 pts) ──
    total = news_count + forum_count
    if total >= 20:
        pts += 30
    elif total >= 10:
        pts += 24
    elif total >= 5:
        pts += 18
    elif total >= 2:
        pts += 12
    elif total >= 1:
        pts += 6

    # ── Signal score bonus (20 pts) ──
    sig = _safe_float(signal_score)
    if sig > 0:
        pts += min(20, sig * 20)  # signal_score is typically 0-1
    elif total > 0:
        pts += 10  # some data present

    score = _clamp(pts) if total > 0 else _clamp(10)
    return {"score": score, "label": _label(score)}


def score_internal_knowledge(
    *,
    key_findings_count: int = 0,
    has_recommendations: bool = False,
    confidence: str = "medium",
    source_type: str = "internal_database",
) -> Dict[str, Any]:
    """Score internal knowledge availability."""
    pts = 0.0

    # ── Findings richness (50 pts) ──
    if key_findings_count >= 5:
        pts += 50
    elif key_findings_count >= 3:
        pts += 38
    elif key_findings_count >= 1:
        pts += 22
    else:
        pts += 5  # no findings but agent ran

    # ── Recommendations (25 pts) ──
    if has_recommendations:
        pts += 25
    else:
        pts += 5

    # ── Confidence (25 pts) ──
    conf = (confidence or "medium").lower()
    if conf == "high":
        pts += 25
    elif conf == "medium":
        pts += 15
    else:
        pts += 8

    score = _clamp(pts)
    return {"score": score, "label": _label(score)}


# ═════════════════════════════════════════════════════════════════════════════
#  Composite helpers
# ═════════════════════════════════════════════════════════════════════════════

def _label(score: int) -> str:
    """Human-readable label for a score."""
    if score == 0:
        return "Critical Blocker"
    if score <= 20:
        return "Very Unfavourable"
    if score <= 40:
        return "Unfavourable"
    if score <= 60:
        return "Neutral"
    if score <= 80:
        return "Favourable"
    return "Highly Favourable"


def check_critical_blockers(agent_scores: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return list of agents that scored 0 (critical blockers).

    Each entry: ``{"agent": <key>, "reason": <str>}``
    """
    blockers = []
    for key, info in agent_scores.items():
        if info.get("score") == 0:
            blockers.append({
                "agent": key,
                "reason": info.get("criticalReason", "Critical blocker detected"),
            })
    return blockers
