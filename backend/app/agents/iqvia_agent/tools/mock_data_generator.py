"""
IQVIA Mock Data Generator

Generates realistic pharmaceutical market data for visualization
when live/cached data is unavailable. Uses LLM-derived context
about the drug/indication to produce plausible figures.

All values are clearly marked as illustrative estimates.
"""

from __future__ import annotations

import hashlib
import random
from typing import Optional


def _seeded_rng(seed_str: str) -> random.Random:
    """Return a deterministic Random instance so the same query always yields the same mock data."""
    h = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
    return random.Random(h)


# ── Therapy-area heuristics for realistic ranges ──────────────────────────────

_THERAPY_PROFILES = {
    "oncology": {"base_market": (40, 120), "cagr": (8, 16), "leaders": [
        ("Roche", 18), ("Merck & Co.", 15), ("Bristol-Myers Squibb", 13),
        ("AstraZeneca", 11), ("Pfizer", 9), ("Others", 34),
    ]},
    "diabetes": {"base_market": (30, 80), "cagr": (7, 14), "leaders": [
        ("Novo Nordisk", 35), ("Eli Lilly", 25), ("Sanofi", 12),
        ("AstraZeneca", 8), ("Others", 20),
    ]},
    "cardiovascular": {"base_market": (20, 55), "cagr": (4, 9), "leaders": [
        ("Pfizer", 16), ("Novartis", 14), ("AstraZeneca", 12),
        ("Bayer", 10), ("Others", 48),
    ]},
    "immunology": {"base_market": (25, 70), "cagr": (6, 12), "leaders": [
        ("AbbVie", 28), ("Johnson & Johnson", 16), ("Amgen", 11),
        ("Novartis", 9), ("Others", 36),
    ]},
    "neurology": {"base_market": (15, 45), "cagr": (5, 11), "leaders": [
        ("Biogen", 18), ("Roche", 14), ("Eisai", 10),
        ("Eli Lilly", 9), ("Others", 49),
    ]},
    "respiratory": {"base_market": (18, 50), "cagr": (5, 10), "leaders": [
        ("AstraZeneca", 22), ("GSK", 18), ("Boehringer Ingelheim", 14),
        ("Sanofi/Regeneron", 11), ("Others", 35),
    ]},
    "rare_disease": {"base_market": (5, 25), "cagr": (10, 20), "leaders": [
        ("Vertex", 20), ("BioMarin", 14), ("Alexion/AstraZeneca", 13),
        ("Sarepta", 8), ("Others", 45),
    ]},
    "infectious_disease": {"base_market": (15, 45), "cagr": (4, 9), "leaders": [
        ("Gilead Sciences", 22), ("Pfizer", 16), ("Merck & Co.", 13),
        ("GSK", 10), ("Others", 39),
    ]},
    "obesity": {"base_market": (10, 40), "cagr": (15, 30), "leaders": [
        ("Novo Nordisk", 55), ("Eli Lilly", 30),
        ("Others", 15),
    ]},
    "dermatology": {"base_market": (12, 35), "cagr": (6, 12), "leaders": [
        ("AbbVie", 22), ("Johnson & Johnson", 15), ("Leo Pharma", 10),
        ("Amgen", 9), ("Others", 44),
    ]},
    "gastroenterology": {"base_market": (10, 30), "cagr": (5, 10), "leaders": [
        ("AbbVie", 24), ("Takeda", 18), ("Johnson & Johnson", 14),
        ("Pfizer", 10), ("Others", 34),
    ]},
    "ophthalmology": {"base_market": (8, 25), "cagr": (5, 10), "leaders": [
        ("Roche/Genentech", 30), ("Regeneron", 25), ("Bayer", 14),
        ("Novartis", 12), ("Others", 19),
    ]},
}

# Keyword → therapy-area mapping for smart detection
_KEYWORD_THERAPY_MAP = {
    "cancer": "oncology", "tumor": "oncology", "carcinoma": "oncology",
    "lymphoma": "oncology", "leukemia": "oncology", "melanoma": "oncology",
    "sarcoma": "oncology", "glioblastoma": "oncology", "myeloma": "oncology",
    "breast": "oncology", "lung": "oncology", "colon": "oncology",
    "prostate": "oncology", "ovarian": "oncology", "pancreatic": "oncology",
    "pembrolizumab": "oncology", "nivolumab": "oncology", "atezolizumab": "oncology",
    "trastuzumab": "oncology", "bevacizumab": "oncology",

    "diabetes": "diabetes", "insulin": "diabetes", "metformin": "diabetes",
    "glp-1": "diabetes", "glp1": "diabetes", "semaglutide": "diabetes",
    "tirzepatide": "diabetes", "ozempic": "diabetes", "mounjaro": "diabetes",
    "hyperglycemia": "diabetes", "hba1c": "diabetes",

    "cardiovascular": "cardiovascular", "hypertension": "cardiovascular",
    "heart": "cardiovascular", "cardiac": "cardiovascular", "statin": "cardiovascular",
    "cholesterol": "cardiovascular", "atherosclerosis": "cardiovascular",
    "anticoagulant": "cardiovascular", "thrombosis": "cardiovascular",

    "autoimmune": "immunology", "rheumatoid": "immunology", "lupus": "immunology",
    "psoriasis": "immunology", "crohn": "immunology", "colitis": "immunology",
    "adalimumab": "immunology", "humira": "immunology", "biologics": "immunology",

    "alzheimer": "neurology", "parkinson": "neurology", "epilepsy": "neurology",
    "multiple sclerosis": "neurology", "migraine": "neurology", "dementia": "neurology",
    "neurodegeneration": "neurology", "neuropathy": "neurology",

    "asthma": "respiratory", "copd": "respiratory", "pulmonary": "respiratory",
    "fibrosis": "respiratory", "bronchitis": "respiratory",

    "rare": "rare_disease", "orphan": "rare_disease", "gene therapy": "rare_disease",

    "hiv": "infectious_disease", "hepatitis": "infectious_disease",
    "antibiotic": "infectious_disease", "antiviral": "infectious_disease",
    "antimicrobial": "infectious_disease", "infection": "infectious_disease",
    "azithromycin": "infectious_disease", "amoxicillin": "infectious_disease",

    "obesity": "obesity", "weight": "obesity", "bmi": "obesity",
    "wegovy": "obesity", "saxenda": "obesity", "contrave": "obesity",

    "eczema": "dermatology", "atopic": "dermatology", "acne": "dermatology",
    "skin": "dermatology", "dermatitis": "dermatology",

    "ibd": "gastroenterology", "irritable bowel": "gastroenterology",
    "ulcer": "gastroenterology", "gerd": "gastroenterology",

    "macular": "ophthalmology", "retina": "ophthalmology", "glaucoma": "ophthalmology",
    "eye": "ophthalmology", "vision": "ophthalmology",
}


def _detect_therapy_area(
    drug_name: Optional[str],
    therapy_area: Optional[str],
    indication: Optional[str],
) -> str:
    """Best-effort therapy-area detection from available context."""
    # 1. Explicit therapy area provided
    if therapy_area:
        key = therapy_area.lower().replace(" ", "_").replace("-", "_")
        if key in _THERAPY_PROFILES:
            return key
        # Fuzzy match
        for profile_key in _THERAPY_PROFILES:
            if profile_key in key or key in profile_key:
                return profile_key

    # 2. Keyword scan across drug + indication
    combined = " ".join(filter(None, [drug_name, indication, therapy_area])).lower()
    for keyword, area in _KEYWORD_THERAPY_MAP.items():
        if keyword in combined:
            return area

    # 3. Fallback — general pharma profile
    return "oncology"  # most common query type


def generate_mock_market_data(
    drug_name: str,
    therapy_area: Optional[str] = None,
    indication: Optional[str] = None,
) -> dict:
    """
    Generate realistic mock market data for a drug/therapy query.

    Returns the same schema as a successful ``fetch_market_data`` call,
    so the rest of the agent pipeline (CAGR, visualizations) works
    identically.

    The data is deterministic per query string so repeated calls
    produce the same numbers.
    """
    detected_area = _detect_therapy_area(drug_name, therapy_area, indication)
    profile = _THERAPY_PROFILES[detected_area]

    seed = f"{drug_name}:{therapy_area}:{indication}".lower()
    rng = _seeded_rng(seed)

    # ── Market forecast ────────────────────────────────────────────
    base_low, base_high = profile["base_market"]
    base_value = round(rng.uniform(base_low, base_high), 1)

    cagr_low, cagr_high = profile["cagr"]
    cagr = round(rng.uniform(cagr_low, cagr_high), 1)
    annual_growth = 1 + cagr / 100

    # Generate 6 years of data (3 historical + 3 forecast)
    base_year = 2022
    forecast_data = []
    val = base_value
    for i in range(6):
        forecast_data.append({
            "year": str(base_year + i),
            "value": round(val, 1),
        })
        val *= annual_growth
        # Add slight randomness to growth each year (±1pp)
        val *= 1 + rng.uniform(-0.01, 0.01)

    # Pretty title
    area_label = detected_area.replace("_", " ").title()
    drug_label = (drug_name or "").title()
    forecast_title = f"Global {area_label} Market Forecast — {drug_label} Segment (USD Billions)"
    forecast_desc = (
        f"Illustrative market projection for the {area_label.lower()} segment "
        f"relevant to {drug_label}. Based on industry benchmarks and analyst consensus ranges. "
        f"Estimated CAGR ~{cagr}%."
    )

    # ── Competitive share (use profile leaders with light jitter) ──
    leaders = []
    remaining = 100.0
    for company, base_share in profile["leaders"][:-1]:  # all except "Others"
        jittered = max(1, round(base_share + rng.uniform(-3, 3), 0))
        jittered = min(jittered, remaining - 1)
        leaders.append({"company": company, "share": f"~{int(jittered)}%"})
        remaining -= jittered
    # "Others" gets the remainder
    others_label = profile["leaders"][-1][0]
    leaders.append({"company": others_label, "share": f"~{int(max(remaining, 1))}%"})

    competitive_title = f"Competitive Market Share — {area_label} ({forecast_data[-3]['year']})"
    competitive_desc = (
        f"Estimated competitive landscape for the {area_label.lower()} market. "
        f"Shares are approximate based on available industry reports."
    )

    return {
        "drug_name": drug_name,
        "therapy_area": therapy_area or area_label,
        "indication": indication or "General",
        "region": "Global",
        "data": {
            "market_forecast": {
                "title": forecast_title,
                "data": forecast_data,
                "description": forecast_desc,
            },
            "competitive_share": {
                "title": competitive_title,
                "data": leaders,
                "description": competitive_desc,
            },
        },
        "matched_key": f"mock_{detected_area}",
        "data_source": "Illustrative Estimate (Industry Benchmarks)",
        "note": "This is illustrative data generated from industry benchmarks because specific market data was not available. Values should be validated with actual market reports.",
        "is_mock": True,
    }


def generate_mock_cagr(market_data: dict) -> Optional[dict]:
    """Compute CAGR from the mock market_data forecast, matching the schema
    of ``calculate_cagr``."""
    data_section = market_data.get("data", {})
    forecast = data_section.get("market_forecast", {}).get("data", [])
    if len(forecast) < 2:
        return None

    start_val = forecast[0]["value"]
    end_val = forecast[-1]["value"]
    years = len(forecast) - 1

    if start_val <= 0 or years <= 0:
        return None

    cagr_pct = ((end_val / start_val) ** (1 / years) - 1) * 100
    total_growth = ((end_val - start_val) / start_val) * 100

    return {
        "start_value": start_val,
        "end_value": end_val,
        "years": years,
        "cagr_percent": round(cagr_pct, 2),
        "total_growth_percent": round(total_growth, 2),
        "interpretation": (
            f"The market is projected to grow from ${start_val}B to ${end_val}B "
            f"over {years} years, representing a CAGR of ~{cagr_pct:.1f}%."
        ),
    }
