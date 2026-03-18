"""
FTO Score Normalizer

Translates raw FTO scores into a stable 0-100 FTO Risk Index with risk bands.

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT CHANGES (Jan 2026):
- normalizedRiskInternal: 0-100 integer for internal sorting ONLY
- riskBand per-patent: CLEAR / LOW / MODERATE / HIGH / CRITICAL
- ftoStatus overall: CLEAR / LOW_RISK / MODERATE_RISK / HIGH_RISK / CRITICAL_RISK
- Raw numeric scores are NOT exposed to UI (internal only)
═══════════════════════════════════════════════════════════════════════════════

SCORING NORMALIZATION:
- Raw scores vary based on number of patents analyzed
- Normalized index provides consistent 0-100 scale for UI/comparisons
- Risk bands give clear human-readable risk levels

ALGORITHM:
- perPatentCap = 12 (matches fto_decision_engine per-patent cap)
- max_possible_raw = perPatentCap * max(1, num_patents)
- normalized = round(min(raw_total / max_possible_raw * 100, 100))

BAND MAPPING (updated for CLEAR at 0):
- 0:      CLEAR     - No blocking patents
- 1-25:   LOW       - Minor blocking concerns
- 26-50:  MODERATE  - Some blocking patents, counsel recommended
- 51-75:  HIGH      - Significant blocking, licensing likely needed
- 76-100: CRITICAL  - Multiple severe blockers, licensing required
"""

from typing import Dict, Any

# Per-patent score cap (matches fto_decision_engine)
PER_PATENT_CAP = 12

# Risk band thresholds (updated per spec: 0=CLEAR, 1-25=LOW, 26-50=MODERATE, 51-75=HIGH, 76-100=CRITICAL)
RISK_BANDS = {
    "CLEAR": (0, 0),
    "LOW": (1, 25),
    "MODERATE": (26, 50),
    "HIGH": (51, 75),
    "CRITICAL": (76, 100),
}

# Mapping from band to ftoStatus (matches frontend status config)
BAND_TO_FTO_STATUS = {
    "CLEAR": "CLEAR",
    "LOW": "NEEDS_MONITORING",
    "MODERATE": "AT_RISK",
    "HIGH": "BLOCKED",
    "CRITICAL": "BLOCKED",
}


def normalize_raw_score(raw_total: float, num_patents: int) -> Dict[str, Any]:
    """
    Normalize raw FTO score to a 0-100 index with risk band.
    
    Args:
        raw_total: Raw score sum from fto_decision_engine
        num_patents: Number of patents analyzed
    
    Returns:
        {
            "normalizedRiskInternal": int (0-100) - INTERNAL ONLY, not for UI display
            "band": str ("CLEAR", "LOW", "MODERATE", "HIGH", "CRITICAL"),
            "ftoStatus": str (e.g. "HIGH_RISK") - for frontend display
            "details": { ... } - internal audit data
        }
    
    NOTE: normalizedRiskInternal is for INTERNAL SORTING ONLY.
    Frontend should NOT display this as a numeric score.
    Use ftoStatus and band for user-facing risk communication.
    
    Edge Cases:
        - num_patents == 0: returns normalizedRiskInternal=0, band="CLEAR"
        - raw_total == 0: returns normalizedRiskInternal=0, band="CLEAR"
    """
    # Edge case: no patents or zero score = CLEAR
    if num_patents <= 0 or raw_total <= 0:
        return {
            "normalizedRiskInternal": 0,
            "band": "CLEAR",
            "ftoStatus": "CLEAR",
            "details": {
                "rawScore": raw_total,
                "numPatents": num_patents,
                "maxPossibleRaw": 0,
                "perPatentCap": PER_PATENT_CAP,
                "formula": "No patents analyzed or zero score - CLEAR"
            }
        }
    
    # Calculate max possible raw score
    max_possible_raw = PER_PATENT_CAP * max(1, num_patents)
    
    # Normalize to 0-100 scale
    normalized = round(min((raw_total / max_possible_raw) * 100, 100))
    
    # Determine risk band
    band = _determine_band(normalized)
    
    # Map to ftoStatus for frontend
    fto_status = BAND_TO_FTO_STATUS.get(band, "HIGH_RISK")
    
    return {
        "normalizedRiskInternal": normalized,
        "band": band,
        "ftoStatus": fto_status,
        "details": {
            "rawScore": raw_total,
            "numPatents": num_patents,
            "maxPossibleRaw": max_possible_raw,
            "perPatentCap": PER_PATENT_CAP,
            "formula": f"round(min({raw_total}/{max_possible_raw}*100, 100)) = {normalized}"
        }
    }


def _determine_band(normalized: int) -> str:
    """Map normalized index (0-100) to risk band."""
    if normalized == 0:
        return "CLEAR"
    elif normalized <= 25:
        return "LOW"
    elif normalized <= 50:
        return "MODERATE"
    elif normalized <= 75:
        return "HIGH"
    else:
        return "CRITICAL"


def get_band_description(band: str) -> str:
    """Get human-readable description for a risk band."""
    descriptions = {
        "CLEAR": "No blocking patents identified. Proceed with standard IP monitoring.",
        "LOW": "Minor blocking patent concerns. Proceed with caution and monitor landscape.",
        "MODERATE": "Some blocking patents present. Recommend detailed FTO opinion from patent counsel.",
        "HIGH": "Significant blocking patents identified. Licensing negotiations likely required.",
        "CRITICAL": "Multiple severe blocking patents. Licensing required before proceeding.",
    }
    return descriptions.get(band, "Unknown risk level")


def get_band_color(band: str) -> str:
    """Get UI color for risk band (for visualization)."""
    colors = {
        "CLEAR": "#22c55e",    # Green
        "LOW": "#84cc16",      # Lime green
        "MODERATE": "#f59e0b", # Amber
        "HIGH": "#f97316",     # Orange
        "CRITICAL": "#ef4444", # Red
    }
    return colors.get(band, "#6b7280")  # Gray default


def normalize_patent_risk(raw_score: float, blocks_use: bool = None, status: str = None) -> Dict[str, Any]:
    """
    Normalize a single patent's risk score to 0-100 scale with riskBand.
    
    This function is used to assign per-patent riskBand values.
    
    Args:
        raw_score: Raw risk score (0-12 typically)
        blocks_use: Whether patent blocks use (True/False/None)
        status: Patent status string
    
    Returns:
        {
            "normalizedRisk": int (0-100) - internal only
            "riskBand": str (CLEAR/LOW/MODERATE/HIGH/CRITICAL)
        }
    """
    # Expired or non-blocking patents have CLEAR risk
    if status == "Expired" or blocks_use is False:
        return {"normalizedRisk": 0, "riskBand": "CLEAR"}
    
    # Uncertain patents get MODERATE default
    if blocks_use is None or status == "Uncertain":
        return {"normalizedRisk": 35, "riskBand": "MODERATE"}
    
    # For blocking patents, normalize raw score (capped at PER_PATENT_CAP)
    if raw_score <= 0:
        return {"normalizedRisk": 50, "riskBand": "HIGH"}  # Blocking but no score = default HIGH
    
    # Scale: 0-12 raw → 0-100 normalized
    normalized = round(min((raw_score / PER_PATENT_CAP) * 100, 100))
    
    # Determine band using same logic
    band = _determine_band(normalized)
    
    return {"normalizedRisk": normalized, "riskBand": band}


__all__ = [
    "normalize_raw_score",
    "normalize_patent_risk",
    "get_band_description",
    "get_band_color",
    "PER_PATENT_CAP",
    "RISK_BANDS",
    "BAND_TO_FTO_STATUS",
]
