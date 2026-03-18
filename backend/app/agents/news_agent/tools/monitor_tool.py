"""
Monitor Tool — Core comparator logic for the News Agent.

Functions
---------
extract_assertions(agent_output_or_doc) -> Dict
    Normalize agent data or parsed document into comparable key-values.

compare_assertions(old, new) -> Dict
    Compare two assertion dicts and produce changedFields, severity, diffDetails.

create_or_update_notification(db, sessionId, promptId, compareResult) -> Dict
    Persist or update a notification record in MongoDB.
"""

from __future__ import annotations

import datetime
import re
import uuid
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. extract_assertions
# ---------------------------------------------------------------------------

def extract_assertions(agent_output_or_doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract normalized assertions from agent outputs or a parsed document.

    Input: unwrapped agent data dict  (may contain patent, exim, clinical,
           web_intel, internal_knowledge sub-keys) **or** a document dict
           with ``_raw_text`` key.

    Output: Normalised key-values for comparison:
        {
            "patents": [ {patentNumber, expiry, claimType, title, ...} ],
            "trade": { import_dependency: float, ... },
            "market": { market_size_usd: float, ... },
            "regulatory": [ { keyword, source } ],
            "internal_doc_assertions": [ { statement, entity, ... } ],
            "other_flags": [ ... ]
        }
    """
    if not agent_output_or_doc:
        return _empty_assertions()

    assertions: Dict[str, Any] = _empty_assertions()

    # --- Handle raw text from uploaded doc ---------------------------------
    raw_text = agent_output_or_doc.get("_raw_text")
    if raw_text:
        assertions["internal_doc_assertions"] = _extract_from_raw_text(raw_text)
        assertions["patents"].extend(_extract_patents_from_text(raw_text))
        assertions["regulatory"].extend(_extract_regulatory_from_text(raw_text))
        return assertions

    # --- Handle structured agent outputs -----------------------------------
    _extract_patent_assertions(agent_output_or_doc, assertions)
    _extract_trade_assertions(agent_output_or_doc, assertions)
    _extract_market_assertions(agent_output_or_doc, assertions)
    _extract_regulatory_keywords(agent_output_or_doc, assertions)
    _extract_internal_doc_assertions(agent_output_or_doc, assertions)

    return assertions


def _empty_assertions() -> Dict[str, Any]:
    return {
        "patents": [],
        "trade": {},
        "market": {},
        "regulatory": [],
        "internal_doc_assertions": [],
        "other_flags": [],
    }


# --- Patent extraction helpers ---

def _extract_patent_assertions(data: Dict, out: Dict) -> None:
    """Pull patent info from PATENT_AGENT-style outputs."""
    # Try multiple data shapes
    patent_data = (
        data.get("PATENT_AGENT", {}).get("data", {})
        or data.get("patent", {})
        or data.get("data", {}).get("patent", {})
        or {}
    )
    if isinstance(patent_data, dict) and "data" in patent_data:
        patent_data = patent_data["data"]

    patents_list = (
        patent_data.get("patents", [])
        or patent_data.get("patent_list", [])
        or patent_data.get("fto", {}).get("patents", [])
        or []
    )

    for p in patents_list:
        if not isinstance(p, dict):
            continue
        out["patents"].append({
            "patentNumber": p.get("patentNumber") or p.get("patent_number") or p.get("id", ""),
            "expiry": p.get("expiry") or p.get("expiry_date") or p.get("expirationDate", ""),
            "claimType": p.get("claimType") or p.get("claim_type") or p.get("type", "unknown"),
            "title": p.get("title", ""),
            "blocking": p.get("blocking") or p.get("isBlocking", False),
        })


def _extract_patents_from_text(text: str) -> List[Dict]:
    """Regex-based patent extraction from raw text."""
    results = []
    # Match US patent numbers like US1234567, US12/345,678
    pat_nums = re.findall(r'US[\d,/]{5,}[A-Z]?\d*', text, re.IGNORECASE)
    for pn in pat_nums:
        cleaned = pn.replace(",", "").replace("/", "")
        results.append({
            "patentNumber": cleaned,
            "expiry": "",
            "claimType": "unknown",
            "title": "",
            "blocking": False,
        })

    # Try to find expiry dates near patent numbers
    expiry_matches = re.findall(
        r'(?:expir|valid\s+until|expires?)[\s:]*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        text, re.IGNORECASE
    )
    if expiry_matches and results:
        results[0]["expiry"] = expiry_matches[0]

    # Check for invalidation / blocking language
    if re.search(r'patent\s+.*invalidat', text, re.IGNORECASE):
        for r_ in results:
            r_["claimType"] = "invalidated"
    if re.search(r'blocking\s+patent|patent\s+block', text, re.IGNORECASE):
        for r_ in results:
            r_["blocking"] = True

    return results


# --- Trade / EXIM extraction ---

def _extract_trade_assertions(data: Dict, out: Dict) -> None:
    exim_data = (
        data.get("EXIM_AGENT", {}).get("data", {})
        or data.get("exim", {})
        or {}
    )
    if isinstance(exim_data, dict) and "data" in exim_data:
        exim_data = exim_data["data"]

    llm_insights = exim_data.get("llm_insights", {})
    dep = llm_insights.get("import_dependency", {})

    out["trade"] = {
        "import_dependency": _safe_float(dep.get("dependency_ratio")),
        "yoy_change": _safe_float(dep.get("yoy_change") or exim_data.get("yoy_change")),
        "trade_total": _safe_float(exim_data.get("total_trade_value")),
    }

    # Look for restriction keywords
    risk = llm_insights.get("supply_chain_risk", {})
    if isinstance(risk, dict):
        risk_text = risk.get("risk_level", "")
        if risk_text:
            out["regulatory"].append({"keyword": risk_text, "source": "exim_supply_chain"})


def _extract_market_assertions(data: Dict, out: Dict) -> None:
    iqvia_data = (
        data.get("IQVIA_AGENT", {}).get("data", {})
        or data.get("iqvia", {})
        or {}
    )
    if isinstance(iqvia_data, dict) and "data" in iqvia_data:
        iqvia_data = iqvia_data["data"]

    out["market"] = {
        "market_size_usd": _safe_float(iqvia_data.get("market_size") or iqvia_data.get("market_size_usd")),
        "cagr": _safe_float(iqvia_data.get("cagr") or iqvia_data.get("growth_rate")),
    }


def _extract_regulatory_keywords(data: Dict, out: Dict) -> None:
    """Pull regulatory phrases from web-intel or clinical data."""
    web = (
        data.get("WEB_INTELLIGENCE_AGENT", {}).get("data", {})
        or data.get("web", {})
        or data.get("web_intelligence", {})
        or {}
    )
    if isinstance(web, dict) and "data" in web:
        web = web["data"]

    news = web.get("news", []) or web.get("newsArticles", []) or []
    for article in news[:20]:
        if not isinstance(article, dict):
            continue
        title = article.get("title", "")
        for kw in ["ban", "restrict", "recall", "warning", "embargo", "sanction"]:
            if kw in title.lower():
                out["regulatory"].append({"keyword": kw, "source": title[:80]})


def _extract_internal_doc_assertions(data: Dict, out: Dict) -> None:
    internal = (
        data.get("INTERNAL_KNOWLEDGE_AGENT", {}).get("data", {})
        or data.get("internal_knowledge", {})
        or data.get("internal", {})
        or {}
    )
    if isinstance(internal, dict) and "data" in internal:
        internal = internal["data"]

    synthesis = internal.get("strategic_synthesis", {}) or internal.get("synthesis", {})
    if isinstance(synthesis, dict):
        desc = synthesis.get("description", "")
        if desc:
            out["internal_doc_assertions"].append({
                "statement": desc[:500],
                "entity": "synthesis",
            })


def _extract_from_raw_text(text: str) -> List[Dict]:
    """Extract assertions from unstructured document text."""
    assertions: List[Dict] = []
    lines = text.split("\n")
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or len(line_stripped) < 15:
            continue
        # Look for assertive statements
        if any(kw in line_stripped.lower() for kw in [
            "patent", "expir", "block", "invalidat", "grant",
            "import", "export", "ban", "restrict", "market size",
            "contradict", "recommend", "risk", "approval", "reject",
        ]):
            assertions.append({
                "statement": line_stripped[:500],
                "entity": "document",
            })
    return assertions[:50]  # cap


def _extract_regulatory_from_text(text: str) -> List[Dict]:
    """Pull regulatory phrases from raw text."""
    results = []
    for kw in ["ban", "restrict", "recall", "warning", "embargo", "sanction", "regulatory change"]:
        if kw in text.lower():
            idx = text.lower().index(kw)
            snippet = text[max(0, idx - 40):idx + 60].strip()
            results.append({"keyword": kw, "source": snippet[:100]})
    return results


# ---------------------------------------------------------------------------
# 2. compare_assertions
# ---------------------------------------------------------------------------

def compare_assertions(
    old: Dict[str, Any],
    new: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare two assertion dicts.

    Returns
    -------
    {
        "status": "secure" | "changed" | "error",
        "changedFields": [ "patents", "trade", ... ],
        "severity": "low" | "medium" | "high",
        "diffDetails": {
            fieldName: { oldValue, newValue, note, confidenceScore }
        },
        "requiresManualReview": bool,
        "decision_reason": str
    }
    """
    if not old and not new:
        return _no_change_result("Both old and new assertions empty")

    changed_fields: List[str] = []
    severity_scores: List[str] = []
    diff_details: Dict[str, Any] = {}
    requires_manual = False
    reasons: List[str] = []

    # --- Patent comparison -------------------------------------------------
    patent_diff = _compare_patents(old.get("patents", []), new.get("patents", []))
    if patent_diff["changed"]:
        changed_fields.append("patents")
        severity_scores.append(patent_diff["severity"])
        diff_details["patents"] = patent_diff["details"]
        reasons.append(patent_diff["reason"])
        if patent_diff.get("requiresManualReview"):
            requires_manual = True

    # --- Trade / regulatory comparison -------------------------------------
    trade_diff = _compare_trade(old.get("trade", {}), new.get("trade", {}))
    if trade_diff["changed"]:
        changed_fields.append("trade")
        severity_scores.append(trade_diff["severity"])
        diff_details["trade"] = trade_diff["details"]
        reasons.append(trade_diff["reason"])

    # --- Regulatory keywords -----------------------------------------------
    reg_diff = _compare_regulatory(old.get("regulatory", []), new.get("regulatory", []))
    if reg_diff["changed"]:
        changed_fields.append("regulatory")
        severity_scores.append(reg_diff["severity"])
        diff_details["regulatory"] = reg_diff["details"]
        reasons.append(reg_diff["reason"])

    # --- Internal doc contradictions ----------------------------------------
    doc_diff = _compare_internal_docs(
        old.get("internal_doc_assertions", []),
        new.get("internal_doc_assertions", []),
        old,  # pass full old for cross-check
    )
    if doc_diff["changed"]:
        changed_fields.append("internal_doc")
        severity_scores.append(doc_diff["severity"])
        diff_details["internal_doc"] = doc_diff["details"]
        reasons.append(doc_diff["reason"])
        if doc_diff.get("requiresManualReview"):
            requires_manual = True

    # --- Market size comparison --------------------------------------------
    market_diff = _compare_market(old.get("market", {}), new.get("market", {}))
    if market_diff["changed"]:
        changed_fields.append("market")
        severity_scores.append(market_diff["severity"])
        diff_details["market"] = market_diff["details"]
        reasons.append(market_diff["reason"])

    # --- Aggregate ---------------------------------------------------------
    if not changed_fields:
        return _no_change_result("No material changes detected")

    overall_severity = _max_severity(severity_scores)
    # Conservative default for ambiguous
    if requires_manual and overall_severity == "low":
        overall_severity = "medium"

    return {
        "status": "changed",
        "changedFields": changed_fields,
        "severity": overall_severity,
        "diffDetails": diff_details,
        "requiresManualReview": requires_manual,
        "decision_reason": "; ".join(reasons),
    }


def _no_change_result(reason: str) -> Dict:
    return {
        "status": "secure",
        "changedFields": [],
        "severity": "low",
        "diffDetails": {},
        "requiresManualReview": False,
        "decision_reason": reason,
    }


# --- Patent comparison helpers ---

def _compare_patents(old_patents: List[Dict], new_patents: List[Dict]) -> Dict:
    if not new_patents:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No new patent data"}

    old_numbers = {p.get("patentNumber", "").upper() for p in old_patents if p.get("patentNumber")}
    old_by_num = {p.get("patentNumber", "").upper(): p for p in old_patents if p.get("patentNumber")}

    new_numbers = {p.get("patentNumber", "").upper() for p in new_patents if p.get("patentNumber")}
    new_by_num = {p.get("patentNumber", "").upper(): p for p in new_patents if p.get("patentNumber")}

    added = new_numbers - old_numbers
    removed = old_numbers - new_numbers

    details: Dict[str, Any] = {}
    severity = "low"
    reasons: List[str] = []
    changed = False
    manual_review = False

    # New patents
    for pn in added:
        np = new_by_num[pn]
        claim = np.get("claimType", "unknown")
        blocking = np.get("blocking", False)

        if blocking or claim in ["composition", "method_of_use", "formulation"]:
            # New blocking patent in same claimType → HIGH
            severity = "high"
            reasons.append(f"New blocking patent {pn} (claim: {claim})")
        elif claim in ["unknown"]:
            # Ambiguous → medium + manual review
            severity = max(severity, "medium", key=_sev_key)
            manual_review = True
            reasons.append(f"New patent {pn} with unknown claim type — manual review needed")
        else:
            # Non-blocking addition → low
            reasons.append(f"New non-blocking patent {pn} (claim: {claim})")

        details[pn] = {
            "oldValue": None,
            "newValue": np,
            "note": f"New patent detected: {pn}",
            "confidenceScore": 0.9 if claim != "unknown" else 0.5,
        }
        changed = True

    # Changed expiry dates
    for pn in old_numbers & new_numbers:
        old_exp = old_by_num[pn].get("expiry", "")
        new_exp = new_by_num[pn].get("expiry", "")
        if old_exp and new_exp and old_exp != new_exp:
            severity = max(severity, "medium", key=_sev_key)
            reasons.append(f"Patent {pn} expiry changed: {old_exp} → {new_exp}")
            details[f"{pn}_expiry"] = {
                "oldValue": old_exp,
                "newValue": new_exp,
                "note": "Expiry date change detected",
                "confidenceScore": 0.85,
            }
            changed = True

    if not changed:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No patent changes"}

    return {
        "changed": True,
        "severity": severity,
        "details": details,
        "reason": "; ".join(reasons),
        "requiresManualReview": manual_review,
    }


# --- Trade comparison helpers ---

def _compare_trade(old_trade: Dict, new_trade: Dict) -> Dict:
    if not new_trade or not old_trade:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No trade data to compare"}

    changed = False
    severity = "low"
    details: Dict[str, Any] = {}
    reasons: List[str] = []

    old_dep = _safe_float(old_trade.get("import_dependency"))
    new_dep = _safe_float(new_trade.get("import_dependency"))

    if old_dep is not None and new_dep is not None:
        delta = new_dep - old_dep
        if abs(delta) > 0.10:
            # >10 pp increase → HIGH  (values are ratios, e.g. 0.42 = 42%)
            severity = "high"
            reasons.append(f"Import dependency change: {old_dep*100:.1f}% → {new_dep*100:.1f}% (Δ{delta*100:+.1f}pp)")
            changed = True
            details["import_dependency"] = {
                "oldValue": old_dep,
                "newValue": new_dep,
                "note": f"Import dependency changed by {delta*100:+.1f} percentage points",
                "confidenceScore": 0.9,
            }
        elif abs(delta) > 0.03:
            severity = max(severity, "medium", key=_sev_key)
            reasons.append(f"Import dependency change: {old_dep*100:.1f}% → {new_dep*100:.1f}%")
            changed = True
            details["import_dependency"] = {
                "oldValue": old_dep,
                "newValue": new_dep,
                "note": f"Moderate change in import dependency",
                "confidenceScore": 0.75,
            }

    # YoY sign flip
    old_yoy = _safe_float(old_trade.get("yoy_change"))
    new_yoy = _safe_float(new_trade.get("yoy_change"))
    if old_yoy is not None and new_yoy is not None:
        if (old_yoy > 0 and new_yoy < 0) or (old_yoy < 0 and new_yoy > 0):
            delta_yoy = abs(new_yoy - old_yoy)
            if delta_yoy > 0.20:
                severity = max(severity, "medium", key=_sev_key)
                reasons.append(f"YoY trade change sign flipped: {old_yoy*100:.1f}% → {new_yoy*100:.1f}% (delta {delta_yoy*100:.0f}pp)")
                changed = True
                details["yoy_change"] = {
                    "oldValue": old_yoy,
                    "newValue": new_yoy,
                    "note": "Year-over-year trade change sign flip with large magnitude",
                    "confidenceScore": 0.8,
                }

    if not changed:
        return {"changed": False, "severity": "low", "details": {}, "reason": "Trade data stable"}

    return {"changed": True, "severity": severity, "details": details, "reason": "; ".join(reasons)}


# --- Regulatory comparison ---

def _compare_regulatory(old_reg: List[Dict], new_reg: List[Dict]) -> Dict:
    if not new_reg:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No new regulatory flags"}

    old_kws = {r.get("keyword", "").lower() for r in old_reg}
    new_kws = {r.get("keyword", "").lower() for r in new_reg}

    added_kws = new_kws - old_kws
    high_severity_kws = {"ban", "embargo", "sanction", "recall"}

    if not added_kws:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No new regulatory keywords"}

    high_hits = added_kws & high_severity_kws
    severity = "high" if high_hits else "medium"

    details: Dict[str, Any] = {}
    for kw in added_kws:
        source_entries = [r for r in new_reg if r.get("keyword", "").lower() == kw]
        details[kw] = {
            "oldValue": None,
            "newValue": kw,
            "note": f"New regulatory keyword: {kw}",
            "confidenceScore": 0.7,
            "sources": [s.get("source", "") for s in source_entries][:3],
        }

    return {
        "changed": True,
        "severity": severity,
        "details": details,
        "reason": f"New regulatory keywords detected: {', '.join(added_kws)}",
    }


# --- Internal doc contradictions ---

def _compare_internal_docs(
    old_docs: List[Dict],
    new_docs: List[Dict],
    old_full: Dict,
) -> Dict:
    if not new_docs:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No new document assertions"}

    changed = False
    severity = "low"
    details: Dict[str, Any] = {}
    reasons: List[str] = []
    manual_review = False

    # Check for contradiction patterns
    contradiction_patterns = [
        (r"patent\s+.*invalidat", "Patent invalidation detected"),
        (r"not\s+block", "Non-blocking assertion detected"),
        (r"approv.*reject|reject.*approv", "Approval/rejection contradiction"),
        (r"recall|withdraw", "Product recall/withdrawal"),
        (r"contradict", "Explicit contradiction"),
    ]

    old_stmts = " ".join(d.get("statement", "") for d in old_docs).lower()
    new_stmts = [d.get("statement", "") for d in new_docs]

    for new_stmt in new_stmts:
        stmt_lower = new_stmt.lower()
        for pattern, description in contradiction_patterns:
            if re.search(pattern, stmt_lower, re.IGNORECASE):
                # Check if this contradicts old data
                # e.g. old says "blocking patent" but new says "patent invalidated"
                if _detect_contradiction(old_full, new_stmt):
                    severity = "high"
                    reasons.append(f"Contradiction: {description}")
                    details[f"contradiction_{len(details)}"] = {
                        "oldValue": old_stmts[:200] if old_stmts else "N/A",
                        "newValue": new_stmt[:200],
                        "note": description,
                        "confidenceScore": 0.6,
                    }
                    changed = True
                    manual_review = True
                else:
                    # Ambiguous — conservative default
                    severity = max(severity, "medium", key=_sev_key)
                    manual_review = True
                    reasons.append(f"Possible contradiction: {description} — requires manual review")
                    details[f"possible_contradiction_{len(details)}"] = {
                        "oldValue": old_stmts[:200] if old_stmts else "N/A",
                        "newValue": new_stmt[:200],
                        "note": f"{description} — ambiguous, manual review recommended",
                        "confidenceScore": 0.4,
                    }
                    changed = True

    if not changed and new_docs:
        # New document info exists but no contradictions — still flag as informational
        details["new_info"] = {
            "oldValue": None,
            "newValue": f"{len(new_docs)} new assertions from uploaded document",
            "note": "New document information available — no contradictions detected",
            "confidenceScore": 0.9,
        }
        # Don't mark as high severity for informational
        return {"changed": False, "severity": "low", "details": details, "reason": "New doc info, no contradictions"}

    if not changed:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No doc contradictions"}

    return {
        "changed": True,
        "severity": severity,
        "details": details,
        "reason": "; ".join(reasons),
        "requiresManualReview": manual_review,
    }


def _detect_contradiction(old_full: Dict, new_statement: str) -> bool:
    """Heuristic check whether new_statement contradicts old assertions."""
    stmt_lower = new_statement.lower()

    # If old data has blocking patents and new doc says they're invalidated
    old_patents = old_full.get("patents", [])
    has_blocking = any(p.get("blocking") for p in old_patents)

    if has_blocking and re.search(r"invalidat|overturn|revok", stmt_lower):
        return True

    # If old data suggests clear FTO and new doc says blocking
    has_clear = all(not p.get("blocking") for p in old_patents) if old_patents else False
    if has_clear and re.search(r"block|infring", stmt_lower):
        return True

    return False


# --- Market comparison ---

def _compare_market(old_market: Dict, new_market: Dict) -> Dict:
    if not old_market or not new_market:
        return {"changed": False, "severity": "low", "details": {}, "reason": "No market data to compare"}

    old_size = _safe_float(old_market.get("market_size_usd"))
    new_size = _safe_float(new_market.get("market_size_usd"))

    if old_size and new_size and old_size > 0:
        pct_change = abs(new_size - old_size) / old_size * 100
        if pct_change > 30:
            return {
                "changed": True,
                "severity": "medium",
                "details": {
                    "market_size_usd": {
                        "oldValue": old_size,
                        "newValue": new_size,
                        "note": f"Market size changed by {pct_change:.1f}%",
                        "confidenceScore": 0.7,
                    }
                },
                "reason": f"Market size changed significantly ({pct_change:.1f}%)",
            }

    return {"changed": False, "severity": "low", "details": {}, "reason": "Market data stable"}


# ---------------------------------------------------------------------------
# 3. create_or_update_notification
# ---------------------------------------------------------------------------

def create_or_update_notification(
    db,
    session_id: str,
    prompt_id: str,
    compare_result: Dict[str, Any],
    tag_name: str = "",
) -> Dict[str, Any]:
    """Create or update a notification record in MongoDB.

    Uses the ``notifications`` collection.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    existing = db.db["notifications"].find_one({
        "sessionId": session_id,
        "promptId": prompt_id,
    })

    notification_data = {
        "sessionId": session_id,
        "promptId": prompt_id,
        "tagName": tag_name or (existing or {}).get("tagName", ""),
        "enabled": (existing or {}).get("enabled", True),
        "lastCheckedAt": now,
        "status": compare_result.get("status", "secure"),
        "severity": compare_result.get("severity", "low"),
        "changedFields": compare_result.get("changedFields", []),
        "details": compare_result.get("diffDetails", {}),
        "requiresManualReview": compare_result.get("requiresManualReview", False),
        "decision_reason": compare_result.get("decision_reason", ""),
        "updatedAt": now,
    }

    if existing:
        db.db["notifications"].update_one(
            {"_id": existing["_id"]},
            {"$set": notification_data},
        )
        notification_data["notificationId"] = existing.get("notificationId", str(existing["_id"]))
    else:
        notification_data["notificationId"] = str(uuid.uuid4())
        notification_data["createdAt"] = now
        db.db["notifications"].insert_one(notification_data)

    # Remove MongoDB _id for JSON serialisation
    notification_data.pop("_id", None)
    return notification_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


def _sev_key(s: str) -> int:
    return _SEVERITY_ORDER.get(s, 0)


def _max_severity(sevs: List[str]) -> str:
    if not sevs:
        return "low"
    return max(sevs, key=_sev_key)
