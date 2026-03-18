from __future__ import annotations

import json

from crewai import Agent, LLM

from app.services.viz_builder import build_exim_visualizations
from app.services.agent_scorer import score_exim
from .tools.fetch_exim_data import fetch_exim_data, _fetch_exim_data_impl

llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=400)
llm_large = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=4096)

exim_agent = Agent(
    role="EXIM Trends Agent",
    goal="Analyze pharmaceutical export-import trends using India TradeStats data",
    backstory="""You are an expert in international pharmaceutical trade analysis.
    
    RESPONSIBILITIES
    - Analyze export/import trade data for pharmaceutical products
    - Track trade volumes and growth trends across years
    - Identify key trading partners and market shares
    - Provide strategic sourcing insights
    
    HARD RULES (DO NOT VIOLATE)
    - NEVER invent trade values, HS codes, or country data
    - If tools return no data, clearly state: "No trade data available for this query"
    - Prefer tool outputs over model guesses; clearly label every data source
    - Separate facts (from tools) vs. analysis (your reasoning)
    
    REQUIRED OUTPUT SECTIONS
    - Trade Volume Summary (current year vs previous year)
    - Top Trading Partners (by trade value)
    - Growth Analysis (YoY growth percentages)
    - Data Sources (explicitly list which tools/APIs were used)
    
    ERROR / NO-DATA HANDLING
    - If no trade data found: clearly say "No trade data available" and explain the limitation
    - If partial data: return whatever is available; mark missing fields as "unknown"
    """,
    tools=[fetch_exim_data],
    verbose=True,
    allow_delegation=False,
    llm=llm,
)


# HSN Code mapping for pharmaceutical products
PHARMA_HSN_CODES = {
    # Bulk drugs & APIs
    "paracetamol": "29242990",
    "ibuprofen": "29163990",
    "metformin": "29252990",
    "amoxicillin": "29411090",
    "azithromycin": "29419090",
    "omeprazole": "29349990",
    "atorvastatin": "29362990",
    "ciprofloxacin": "29419090",
    "amlodipine": "29339990",
    "losartan": "29339990",
    # Formulations & finished drugs
    "medicines": "30049099",
    "pharmaceuticals": "30049099",
    "drugs": "30049099",
    "tablets": "30049099",
    "capsules": "30049099",
    "injections": "30049099",
    "formulations": "30049099",
    "vaccines": "30022090",
    "insulin": "30043100",
    "antibiotics": "30041090",
    # Generic categories
    "api": "29419090",
    "bulk drugs": "29419090",
    "active pharmaceutical ingredients": "29419090",
    "pharmaceutical intermediates": "29339990",
    # Default for general pharma queries
    "default": "30049099",
}


def _get_hsn_code(query: str) -> str:
    """Get HSN code from query keywords."""
    query_lower = query.lower()
    for keyword, code in PHARMA_HSN_CODES.items():
        if keyword in query_lower:
            return code
    return PHARMA_HSN_CODES["default"]


def _build_exim_summary(trade_volume: dict, top_partners: list, trade_type: str, product: str) -> dict:
    """Build canonical summary object for the banner."""
    total_value = trade_volume.get("total_value_usd_million", 0)
    yoy_growth = trade_volume.get("yoy_growth_percent", 0)
    
    has_data = total_value > 0 or len(top_partners) > 0
    is_growing = yoy_growth > 5 if yoy_growth else False
    
    if has_data:
        summary_answer = "Yes" if is_growing else "Stable"
    else:
        summary_answer = "No"
    
    summary = {
        "researcherQuestion": f"Is there active {trade_type} trade for this product?",
        "answer": summary_answer,
        "explainers": []
    }
    
    if total_value:
        summary["explainers"].append(f"Trade value: ${total_value:,.0f}M")
    if yoy_growth is not None:
        summary["explainers"].append(f"YoY growth: {yoy_growth:.1f}%")
    if top_partners:
        top_partner = top_partners[0].get("name", "Unknown") if top_partners else None
        if top_partner:
            summary["explainers"].append(f"Top partner: {top_partner}")

    # ── Feasibility score ──
    _exim_score = score_exim(
        total_value_usd_million=total_value,
        yoy_growth_percent=yoy_growth,
        top_partners_count=len(top_partners),
        trade_type=trade_type,
    )
    summary["feasibilityScore"] = _exim_score

    return summary


def _llm_extract_exim_params(
    user_prompt: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Use the configured LLM to extract hs_code, year, country, trade_type from the prompt."""
    prompt = f"""You are a pharmaceutical trade data extraction expert. Your job is to extract structured information from user queries about export-import trade.

From the following query, extract EXACTLY these 4 fields:
1. product: The pharmaceutical product, drug name, or category mentioned (e.g., 'paracetamol', 'medicines', 'vaccines', 'APIs')
2. year: The financial year mentioned in format 'YYYY-YY' (e.g., '2024-25', '2023-24'). Default to '2024-25' if not specified.
3. country: The country mentioned for trade focus (e.g., 'USA', 'Germany', 'China'). Return 'null' if not specified.
4. trade_type: Either 'export' or 'import' based on the query context. Default to 'export' if not clear.

CRITICAL RULES:
- Extract ONLY what is explicitly stated in the query
- Do NOT make assumptions or invent information
- If a field is not mentioned, return 'null' for that field (except year which defaults to '2024-25' and trade_type which defaults to 'export')
- Product names should be lowercase (e.g., 'paracetamol', 'medicines')
- Year format MUST be 'YYYY-YY' (e.g., '2024-25' not '2024' or '2025')
- Return a valid JSON object with these exact keys

User Query: {user_prompt}

Return ONLY a JSON object, nothing else:"""

    try:
        raw = llm.call(messages=[{"role": "user", "content": prompt}])
    except Exception:
        try:
            raw = llm.call(prompt)
        except Exception as e2:
            print(f"[ERROR] LLM call failed: {e2}")
            return None, "2024-25", None, "export"

    if not isinstance(raw, str):
        raw = str(raw)

    import json as _json

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        print(f"[ERROR] No JSON found in LLM response: {raw}")
        return None, "2024-25", None, "export"

    try:
        data = _json.loads(raw[start : end + 1])
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON from LLM: {e}")
        return None, "2024-25", None, "export"

    def clean_val(val):
        if val is None or (
            isinstance(val, str) and val.lower() in ("null", "none", "")
        ):
            return None
        return val

    product = clean_val(data.get("product"))
    year = clean_val(data.get("year")) or "2024-25"
    country = clean_val(data.get("country"))
    trade_type = clean_val(data.get("trade_type")) or "export"

    print(
        f"[EXIM] LLM raw extracted: product={product}, year={year}, country={country}, trade_type={trade_type}"
    )

    return product, year, country, trade_type


def _llm_generate_exim_data(
    product: str, year: str, country: str | None, trade_type: str
) -> dict:
    """
    Generate EXIM trade data using LLM when API data is unavailable.
    Returns structured data for Trade Volume, Sourcing Insights, and Import Dependency.
    """
    prompt = f"""You are a pharmaceutical trade intelligence expert. Generate realistic export-import trade data for the following query.

Product: {product}
Year: {year}
Country Focus: {country or "Global"}
Trade Type: {trade_type}

Generate a comprehensive JSON response with EXACTLY this structure:
{{
    "trade_volume": {{
        "total_value_usd_million": <number>,
        "previous_year_value": <number>,
        "yoy_growth_percent": <number>,
        "top_exporters": [
            {{"country": "Country Name", "value": <number>, "share": <number>, "growth": <number>}},
            ... (10 countries)
        ],
        "trend_description": "Brief analysis of export trends"
    }},
    "sourcing_insights": {{
        "primary_sources": [
            {{"country": "Country Name", "share_percent": <number>, "quality_rating": "High/Medium/Low", "risk_level": "Low/Medium/High"}},
            ... (5 countries)
        ],
        "supply_concentration": "High/Medium/Low",
        "hhi_index": <number between 0-10000>,
        "diversification_recommendation": "Brief recommendation",
        "description": "Analysis of sourcing patterns and supply chain"
    }},
    "import_dependency": {{
        "critical_dependencies": [
            {{"country": "Country Name", "import_share": <number>, "risk": "High/Medium/Low", "alternative_sources": ["Country1", "Country2"]}},
            ... (top dependencies)
        ],
        "total_import_value_usd_million": <number>,
        "dependency_ratio": <number 0-100>,
        "risk_assessment": "Overall risk assessment description",
        "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"],
        "description": "Analysis of import dependencies and supply chain risks"
    }},
    "summary_description": "Comprehensive 2-3 paragraph summary of the pharmaceutical trade landscape for {product}, including market dynamics, key trends, and strategic insights."
}}

IMPORTANT RULES:
1. Use realistic trade values based on pharmaceutical industry benchmarks
2. Include major pharmaceutical trading nations (India, China, Germany, USA, Switzerland, Belgium, Ireland, UK, France, Italy)
3. Values should be in USD millions
4. Growth rates typically range from -15% to +25% for pharma products
5. Make the data internally consistent (shares should add up reasonably, growth rates should match value changes)
6. For {product}, consider its actual market position and trade patterns

Return ONLY the JSON object, no additional text."""

    try:
        raw = llm_large.call(messages=[{"role": "user", "content": prompt}])
    except Exception:
        try:
            raw = llm_large.call(prompt)
        except Exception as e:
            print(f"[EXIM] LLM fallback failed: {e}")
            return None

    if not isinstance(raw, str):
        raw = str(raw)

    # Extract JSON from response
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        print("[EXIM] No JSON found in LLM fallback response")
        return None

    try:
        data = json.loads(raw[start : end + 1])
        print("[EXIM] LLM fallback generated data successfully")
        return data
    except json.JSONDecodeError as e:
        print(f"[EXIM] Failed to parse LLM fallback JSON: {e}")
        return None


def _build_payload_from_llm_data(
    llm_data: dict, product: str, year: str, country: str | None, trade_type: str
) -> dict:
    """Convert LLM-generated data into the standard payload format."""

    trade_volume = llm_data.get("trade_volume", {})
    sourcing = llm_data.get("sourcing_insights", {})
    dependency = llm_data.get("import_dependency", {})

    # Build top_partners from trade_volume data
    top_partners = []
    for exporter in trade_volume.get("top_exporters", []):
        top_partners.append(
            {
                "name": exporter.get("country", "Unknown"),
                "current_value": exporter.get("value", 0),
                "previous_value": exporter.get("value", 0)
                / (1 + exporter.get("growth", 0) / 100)
                if exporter.get("growth", 0) != -100
                else 0,
                "growth": exporter.get("growth", 0),
                "share": exporter.get("share", 0),
            }
        )

    # Build rows for table display
    rows = []
    for i, partner in enumerate(top_partners, 1):
        rows.append(
            {
                "S.No.": str(i),
                "Country": partner["name"],
                "2024 - 2025": str(round(partner["current_value"], 2)),
                "2023 - 2024": str(round(partner["previous_value"], 2)),
                "%Share": str(round(partner["share"], 2)),
                "%Growth": str(round(partner["growth"], 2)),
            }
        )

    return {
        "summary": _build_exim_summary(trade_volume, top_partners, trade_type, product),
        "input": {
            "product": product,
            "hs_code": _get_hsn_code(product),
            "year": year,
            "country": country,
            "trade_type": trade_type,
        },
        "trade_data": {
            "rows": rows,
            "totals": {
                "Total": str(trade_volume.get("total_value_usd_million", 0)),
            },
            "columns": [
                "S.No.",
                "Country",
                "2023 - 2024",
                "%Share",
                "2024 - 2025",
                "%Growth",
            ],
            "total_records": len(rows),
        },
        "analysis": {
            "summary": {
                "product": product,
                "hs_code": _get_hsn_code(product),
                "year": year,
                "trade_type": trade_type,
                "total_current_year": trade_volume.get("total_value_usd_million", 0),
                "total_previous_year": trade_volume.get("previous_year_value", 0),
                "overall_growth": trade_volume.get("yoy_growth_percent", 0),
                "top_partners_count": len(top_partners),
            },
            "top_partners": top_partners,
            "columns_used": {
                "current_year": "2024 - 2025",
                "previous_year": "2023 - 2024",
                "growth": "%Growth",
                "share": "%Share",
                "country": "Country",
            },
        },
        "llm_insights": {
            "trade_volume_description": trade_volume.get("trend_description", ""),
            "sourcing_insights": {
                "primary_sources": sourcing.get("primary_sources", []),
                "supply_concentration": sourcing.get("supply_concentration", "Medium"),
                "hhi_index": sourcing.get("hhi_index", 0),
                "diversification_recommendation": sourcing.get(
                    "diversification_recommendation", ""
                ),
                "description": sourcing.get("description", ""),
            },
            "import_dependency": {
                "critical_dependencies": dependency.get("critical_dependencies", []),
                "total_import_value": dependency.get(
                    "total_import_value_usd_million", 0
                ),
                "dependency_ratio": dependency.get("dependency_ratio", 0),
                "risk_assessment": dependency.get("risk_assessment", ""),
                "recommendations": dependency.get("recommendations", []),
                "description": dependency.get("description", ""),
            },
            "summary_description": llm_data.get("summary_description", ""),
        },
        "data_source": "LLM-Generated (API data unavailable)",
        "suggestedNextPrompts": [
            {"prompt": f"Show clinical trials for {product}"},
            {"prompt": f"Analyze patents for {product}"},
            {"prompt": f"Compare market size for {product}"}
        ],
    }


def run_exim_agent(
    user_prompt: str,
    *,
    product: str | None = None,
    year: str | None = None,
    country: str | None = None,
    trade_type: str | None = None,
) -> dict:
    """
    Run the EXIM agent.

    If product/year/country/trade_type are provided by orchestrator, use them directly.
    Otherwise, fall back to LLM extraction for backward compatibility.
    """
    print(f"[EXIM] Starting agent with prompt: {user_prompt}")

    # If parameters provided by orchestrator, use them directly
    if product is not None or year is not None or country is not None or trade_type is not None:
        print(
            f"[EXIM] Using orchestrator-provided params: product={product}, year={year}, country={country}, trade_type={trade_type}"
        )
        llm_product = product
        llm_year = year or "2024-25"
        llm_country = country
        llm_trade_type = trade_type or "export"
    else:
        # Fallback to LLM extraction for backward compatibility
        print("[EXIM] No params from orchestrator, falling back to LLM extraction...")
        llm_product, llm_year, llm_country, llm_trade_type = _llm_extract_exim_params(
            user_prompt
        )

    print(
        f"[EXIM] Final params: product={llm_product}, year={llm_year}, country={llm_country}, trade_type={llm_trade_type}"
    )

    # Prefer explicit parameters, then LLM extraction
    prod = product or llm_product or "medicines"
    yr = year or llm_year or "2024-25"
    cntry = country or llm_country
    ttype = trade_type or llm_trade_type or "export"

    # Get HSN code based on product
    hs_code = _get_hsn_code(prod)

    print(f"[EXIM] Using HSN code: {hs_code} for product: {prod}")

    try:
        # Fetch trade data from local data source
        print(
            f"[EXIM] Fetching trade data: year={yr}, hs_code={hs_code}, trade_type={ttype}"
        )

        trade_data = _fetch_exim_data_impl(
            drug_name=prod, hs_code=hs_code, country=cntry
        )

        # Check if API returned valid data
        api_success = "error" not in trade_data and trade_data.get("data") is not None
        
        # Initialize variables outside if block
        rows = []
        totals = {}
        columns = []

        if api_success:
            print("[EXIM] API returned valid data")
            rows = trade_data.get("rows", [])
            totals = trade_data.get("totals", {})
            columns = trade_data.get("columns", [])

            print(f"[EXIM] Found {len(rows)} trade records")

            # If no records found, use LLM fallback
            if len(rows) == 0:
                print("[EXIM] No trade records found in API, using LLM fallback")
                api_success = False
        else:
            print("[EXIM] API returned error or no data, using LLM fallback")

        if api_success:
            # Process trade data for analysis
            processed_data = _process_trade_data(
                rows, columns, prod, hs_code, yr, ttype
            )

            # Build canonical summary object for banner
            total_value = processed_data.get("total_value_current", 0)
            yoy_growth = processed_data.get("yoy_growth", 0)
            top_partners = processed_data.get("top_partners", [])
            
            has_data = total_value > 0 or len(rows) > 0
            is_growing = yoy_growth > 5 if yoy_growth else False
            
            if has_data:
                summary_answer = "Yes" if is_growing else "Stable"
            else:
                summary_answer = "No"
            
            summary = {
                "researcherQuestion": f"Is there active {ttype} trade for this product?",
                "answer": summary_answer,
                "explainers": []
            }
            
            if total_value:
                summary["explainers"].append(f"Trade value: ${total_value:,.0f}" if isinstance(total_value, (int, float)) else f"Trade value: {total_value}")
            if yoy_growth is not None:
                summary["explainers"].append(f"YoY growth: {yoy_growth:.1f}%")
            if top_partners:
                top_partner = top_partners[0].get("country", "Unknown") if top_partners else None
                if top_partner:
                    summary["explainers"].append(f"Top partner: {top_partner}")

            # ── Feasibility score ──
            _exim_score = score_exim(
                total_value_usd_million=total_value if isinstance(total_value, (int, float)) else 0,
                yoy_growth_percent=yoy_growth,
                top_partners_count=len(top_partners),
                trade_type=ttype,
            )
            summary["feasibilityScore"] = _exim_score
            print(f"[EXIM] Feasibility score: {_exim_score['score']}/100 ({_exim_score['label']})")

            # Generate suggested next prompts
            suggested_next_prompts = [
                {"prompt": f"Show clinical trials for {prod}"},
                {"prompt": f"Analyze patents for {prod}"},
                {"prompt": f"Compare market size for {prod}"}
            ]

            payload = {
                "summary": summary,
                "input": {
                    "product": prod,
                    "hs_code": hs_code,
                    "year": yr,
                    "country": cntry,
                    "trade_type": ttype,
                },
                "trade_data": {
                    "rows": rows[:20],
                    "totals": totals,
                    "columns": columns,
                    "total_records": len(rows),
                },
                "analysis": processed_data,
                "data_source": "India TradeStats API",
                "suggestedNextPrompts": suggested_next_prompts,
            }

            return {
                "status": "success",
                "data": payload,
                "visualizations": build_exim_visualizations(payload),
            }
        else:
            # API failed - use LLM fallback
            print(f"[EXIM] API data unavailable, using LLM fallback for: {prod}")

            llm_data = _llm_generate_exim_data(prod, yr, cntry, ttype)

            if llm_data:
                print("[EXIM] LLM successfully generated trade data")
                payload = _build_payload_from_llm_data(llm_data, prod, yr, cntry, ttype)

                return {
                    "status": "success",
                    "data": payload,
                    "visualizations": build_exim_visualizations(payload),
                }
            else:
                print("[EXIM] LLM returned None or empty data")
                return {
                    "status": "error",
                    "message": f"No trade data available for {prod} and LLM fallback failed",
                }
    except Exception as llm_error:
        print(f"[EXIM] LLM fallback failed with error: {llm_error}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"LLM fallback error: {str(llm_error)}",
        }

    except Exception as e:
        print(f"[EXIM] Error: {str(e)}, attempting LLM fallback")
        import traceback

        traceback.print_exc()

        # Try LLM fallback on exception
        try:
            llm_data = _llm_generate_exim_data(prod, yr, cntry, ttype)

            if llm_data:
                payload = _build_payload_from_llm_data(llm_data, prod, yr, cntry, ttype)

                return {
                    "status": "success",
                    "data": payload,
                    "visualizations": build_exim_visualizations(payload),
                }
        except Exception as fallback_error:
            print(f"[EXIM] LLM fallback also failed: {fallback_error}")

        return {"status": "error", "message": str(e)}


def _process_trade_data(
    rows: list, columns: list, product: str, hs_code: str, year: str, trade_type: str
) -> dict:
    """Process raw trade data into structured analysis."""

    # Parse year columns from headers
    # Typical columns: ['S.No.', 'HSCode', 'Commodity', 'Country', '2023 - 2024', '%Share', '2024 - 2025', '%Growth']
    # or: ['S.No.', 'HSCode', 'Commodity', '2023 - 2024', '%Share', '2024 - 2025', '%Growth']

    current_year_col = None
    previous_year_col = None
    growth_col = None
    share_col = None
    country_col = None

    for col in columns:
        col_lower = col.lower()
        if "2024" in col and "2025" in col:
            current_year_col = col
        elif "2023" in col and "2024" in col:
            previous_year_col = col
        elif "growth" in col_lower:
            growth_col = col
        elif "share" in col_lower:
            share_col = col
        elif "country" in col_lower:
            country_col = col

    # Calculate totals and summaries
    total_current = 0.0
    total_previous = 0.0
    top_partners = []

    for row in rows[:20]:  # Top 20 trading partners
        try:
            current_val = (
                float(row.get(current_year_col, "0").replace(",", "") or "0")
                if current_year_col
                else 0
            )
            previous_val = (
                float(row.get(previous_year_col, "0").replace(",", "") or "0")
                if previous_year_col
                else 0
            )
            growth = (
                float(row.get(growth_col, "0").replace(",", "") or "0")
                if growth_col
                else 0
            )
            share = (
                float(row.get(share_col, "0").replace(",", "") or "0")
                if share_col
                else 0
            )

            partner_name = (
                row.get(country_col)
                or row.get("Country")
                or row.get("Commodity", "Unknown")
            )

            top_partners.append(
                {
                    "name": partner_name,
                    "current_value": current_val,
                    "previous_value": previous_val,
                    "growth": growth,
                    "share": share,
                }
            )

            total_current += current_val
            total_previous += previous_val
        except (ValueError, TypeError):
            continue

    # Calculate overall growth
    overall_growth = (
        ((total_current - total_previous) / total_previous * 100)
        if total_previous > 0
        else 0
    )

    return {
        "summary": {
            "product": product,
            "hs_code": hs_code,
            "year": year,
            "trade_type": trade_type,
            "total_current_year": round(total_current, 2),
            "total_previous_year": round(total_previous, 2),
            "overall_growth": round(overall_growth, 2),
            "top_partners_count": len(top_partners),
        },
        "top_partners": top_partners,
        "columns_used": {
            "current_year": current_year_col,
            "previous_year": previous_year_col,
            "growth": growth_col,
            "share": share_col,
            "country": country_col,
        },
    }
