"""
Unified Parameter Extraction Service

Extracts ALL parameters required by all agents in a single LLM call.
This replaces individual agent-level parameter extraction and reduces API calls.

Returns a unified params dict that can be passed to any agent.
"""

from crewai import LLM
import json

llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=1000, temperature=0.3)

UNIFIED_EXTRACTION_PROMPT = """
You are a pharmaceutical analysis parameter extractor.

From the user query below, extract ALL relevant parameters for pharmaceutical agents.

Extract EXACTLY these fields (return null if not mentioned):

1. drug: Drug name or molecule (e.g., "metformin", "pembrolizumab")
2. indication: Disease/condition/indication (e.g., "diabetes", "lung cancer")
3. therapy_area: Therapeutic area (e.g., "Oncology", "Endocrinology", "Cardiovascular")
4. condition: Alias for indication (same as indication)
5. phase: Clinical trial phase ("Phase 1", "Phase 2", "Phase 3", "Phase 4", or "all")
6. trial_status: Trial status ("recruiting", "ongoing", "completed", or null)
7. search_term: Primary search term (usually drug or disease)
8. product: Product name for trade analysis (usually drug)
9. country: Country or region for trade/market analysis
10. year: Financial year in YYYY-YY format (e.g., "2024-25", default "2024-25" if not specified)
11. trade_type: "export" or "import" (default "export")
12. jurisdiction: Patent jurisdiction ("US", "EU", "JP", default "US")

CRITICAL RULES:
- Extract ONLY what is explicitly stated
- Do NOT invent information
- Return valid JSON only
- For numeric/year fields, use appropriate format
- For boolean/enum fields, return exact matching values
- If a field is not mentioned or unclear, return null (except year defaults to "2024-25", jurisdiction to "US", trade_type to "export")
- All string values should be lowercase unless it's a proper name (drug name, country, region)

User Query: {user_prompt}

Return ONLY valid JSON object, nothing else:
"""


def extract_all_parameters(user_prompt: str) -> dict:
    """
    Extract all parameters from user prompt in a single LLM call.

    Returns:
        dict with keys: drug, indication, therapy_area, condition, phase, trial_status,
                       search_term, product, country, year, trade_type, jurisdiction
                       + extraction_status and any errors
    """
    prompt = UNIFIED_EXTRACTION_PROMPT.format(user_prompt=user_prompt)

    try:
        raw = llm.call(prompt)

        if not isinstance(raw, str):
            raw = str(raw)

        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}")

        if start == -1 or end == -1 or end < start:
            print("No JSON found in response, using defaults")
            return _get_default_parameters()

        try:
            params = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            print(f"[PARAM_EXTRACTOR] JSON parse failed: {e}, using defaults")
            return _get_default_parameters()

        # Normalize and add defaults
        params = _normalize_parameters(params)
        params["extraction_status"] = "success"

        print(
            f"[PARAM_EXTRACTOR] Extracted parameters: {_sanitize_for_logging(params)}"
        )
        return params

    except Exception as e:
        print(f"[PARAM_EXTRACTOR] LLM call failed: {e}, using defaults")
        return _get_default_parameters()


def _normalize_parameters(params: dict) -> dict:
    """Normalize extracted parameters with defaults and aliases."""

    # Clean null values
    def clean_val(val):
        if val is None or (
            isinstance(val, str) and val.lower() in ("null", "none", "")
        ):
            return None
        return val

    # Extract values
    drug = clean_val(params.get("drug"))
    indication = clean_val(params.get("indication"))
    therapy_area = clean_val(params.get("therapy_area"))
    condition = clean_val(params.get("condition"))
    phase = clean_val(params.get("phase"))
    trial_status = clean_val(params.get("trial_status"))
    search_term = clean_val(params.get("search_term"))
    product = clean_val(params.get("product"))
    country = clean_val(params.get("country"))
    year = clean_val(params.get("year"))
    trade_type = clean_val(params.get("trade_type"))
    jurisdiction = clean_val(params.get("jurisdiction"))

    # Apply aliases and defaults
    if not indication and condition:
        indication = condition
    if not condition and indication:
        condition = indication

    if not search_term:
        search_term = drug or indication or product

    if not product:
        product = drug

    if not year:
        year = "2024-25"

    if not trade_type:
        trade_type = "export"

    if not jurisdiction:
        jurisdiction = "US"

    # Normalize phase to Title Case
    if phase and phase.lower() != "all":
        if "phase" not in phase.lower():
            phase = f"Phase {phase}".replace("Phase Phase", "Phase")

    # Normalize therapy_area to Title Case
    if therapy_area:
        therapy_area = therapy_area.title()

    return {
        "drug": drug,
        "indication": indication,
        "condition": condition,
        "therapy_area": therapy_area,
        "phase": phase,
        "trial_status": trial_status,
        "search_term": search_term,
        "product": product,
        "country": country,
        "year": year,
        "trade_type": trade_type,
        "jurisdiction": jurisdiction,
    }


def _get_default_parameters() -> dict:
    """Return default parameters when extraction fails."""
    return {
        "drug": None,
        "indication": None,
        "condition": None,
        "therapy_area": None,
        "phase": None,
        "trial_status": None,
        "search_term": None,
        "product": None,
        "country": None,
        "year": "2024-25",
        "trade_type": "export",
        "jurisdiction": "US",
        "extraction_status": "failed_using_defaults",
    }


def _sanitize_for_logging(params: dict) -> dict:
    """Remove None values for cleaner logging."""
    return {k: v for k, v in params.items() if v is not None}
