"""Helpers to standardize visualization payloads for the frontend.

All builders return lightweight dicts with a common shape so the UI can
render charts/tables/cards without agent-specific logic.

This module is designed to be:
- Modular: Each chart type has its own builder
- Generic: Works with any agent data structure
- Robust: Handles missing/null values gracefully
- Consistent: All outputs follow the same schema
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from app.models.visualization import (
    TableColumn,
    Visualization,
    VisualizationType,
    VizConfig,
)


# ============================================================================
# LABEL FORMATTING
# ============================================================================

# Special case mappings for common field names
SPECIAL_LABELS = {
    "nct_id": "NCT ID",
    "id": "ID",
    "url": "URL",
    "api": "API",
    "cagr": "CAGR",
    "roi": "ROI",
    "usd": "USD",
    "eur": "EUR",
    "gbp": "GBP",
    "fda": "FDA",
    "ema": "EMA",
    "moa": "MoA",
    "ip": "IP",
    "r_and_d": "R&D",
    "p_value": "P-Value",
    "ci": "CI",
    "hr": "HR",
    "or": "OR",
}


def _pretty_label(key: str) -> str:
    """Convert field keys to human-readable labels."""
    if not key:
        return ""

    lower = key.lower()
    if lower in SPECIAL_LABELS:
        return SPECIAL_LABELS[lower]

    # Convert snake_case and camelCase to Title Case
    return key.replace("_", " ").replace("-", " ").title()


def build_bar_chart(
    *,
    id: str,
    title: str,
    items: Iterable[dict] | dict,
    x_field: str,
    y_field: str,
    orientation: str = "vertical",
    description: str | None = None,
) -> dict:
    # Accept either a dict mapping or list of dicts
    if isinstance(items, dict):
        data = [{x_field: k, y_field: v} for k, v in items.items()]
    else:
        data = list(items)

    viz = Visualization(
        id=id,
        vizType=VisualizationType.BAR,
        title=title,
        description=description,
        data=data,
        config=VizConfig(
            xField=x_field,
            yField=y_field,
            orientation=orientation,
            legend=False,
            tooltip=True,
        ),
    )
    return viz.model_dump()


def build_pie_chart(
    *,
    id: str,
    title: str,
    items: Iterable[dict] | dict,
    label_field: str = "label",
    value_field: str = "value",
    description: str | None = None,
) -> dict:
    if isinstance(items, dict):
        data = [{label_field: k, value_field: v} for k, v in items.items()]
    else:
        data = list(items)

    viz = Visualization(
        id=id,
        vizType=VisualizationType.PIE,
        title=title,
        description=description,
        data=data,
        config=VizConfig(labelField=label_field, valueField=value_field),
    )
    return viz.model_dump()


def build_table(
    *,
    id: str,
    title: str,
    columns: Sequence[str | Dict[str, str]],
    rows: Sequence[dict],
    description: str | None = None,
    page_size: int = 15,
) -> dict:
    normalized_columns: List[TableColumn] = []
    for col in columns:
        if isinstance(col, str):
            normalized_columns.append(TableColumn(key=col, label=_pretty_label(col)))
        elif isinstance(col, dict):
            key = col.get("key") or col.get("field") or col.get("name")
            if not key:
                continue
            label = col.get("label") or _pretty_label(key)
            col_type = col.get("type")
            normalized_columns.append(TableColumn(key=key, label=label, type=col_type))

    viz = Visualization(
        id=id,
        vizType=VisualizationType.TABLE,
        title=title,
        description=description,
        data={
            "columns": [c.model_dump() for c in normalized_columns],
            "rows": list(rows),
        },
        config=VizConfig(pageSize=page_size, sortable=True),
    )
    return viz.model_dump()


def build_metric_card(
    *,
    id: str,
    title: str,
    value: float | int | str,
    delta: Optional[float] = None,
    unit: str | None = None,
) -> dict:
    viz = Visualization(
        id=id,
        vizType=VisualizationType.CARD,
        title=title,
        data={"value": value, "delta": delta, "unit": unit},
    )
    return viz.model_dump()


def build_clinical_visualizations(payload: dict) -> List[dict]:
    """Create a standard set of visualizations from the clinical agent payload."""
    viz: List[dict] = []

    trials = payload.get("trials", {}) if payload else {}
    analysis = payload.get("analysis", {}) if payload else {}

    phase_dist = trials.get("phase_distribution") or {}
    status_dist = trials.get("status_distribution") or {}
    sponsors = trials.get("top_sponsors") or []
    trials_list = trials.get("trials") or []
    enrollment_summary = trials.get("enrollment_summary") or {}
    total_trials = trials.get("total_trials") or analysis.get("total_trials")
    maturity_score = analysis.get("maturity_score")

    if phase_dist:
        viz.append(
            build_bar_chart(
                id="phase_distribution",
                title="Trial Phase Distribution",
                items=phase_dist,
                x_field="phase",
                y_field="count",
            )
        )

    if status_dist:
        viz.append(
            build_pie_chart(
                id="status_distribution",
                title="Trial Status Breakdown",
                items=status_dist,
            )
        )

    if sponsors:
        sponsor_rows = [
            {"sponsor": s.get("name"), "count": s.get("count")} for s in sponsors if s
        ]
        viz.append(
            build_bar_chart(
                id="top_sponsors",
                title="Top Sponsors",
                items=sponsor_rows,
                x_field="sponsor",
                y_field="count",
                orientation="horizontal",
            )
        )

    if trials_list:
        columns = [
            {"key": "nct_id", "label": "NCT ID"},
            {"key": "title", "label": "Trial Title"},
            {"key": "status", "label": "Status"},
            {"key": "phase", "label": "Phase"},
            {"key": "sponsor", "label": "Sponsor"},
            {"key": "enrollment", "label": "Enrollment"},
            {"key": "locations_count", "label": "Locations"},
        ]
        viz.append(
            build_table(
                id="trials_table",
                title="Clinical Trials",
                columns=columns,
                rows=trials_list,
                page_size=20,
            )
        )

    if total_trials is not None:
        viz.append(
            build_metric_card(
                id="total_trials",
                title="Total Trials",
                value=total_trials,
            )
        )

    if enrollment_summary:
        viz.append(
            build_metric_card(
                id="median_enrollment",
                title="Median Enrollment",
                value=enrollment_summary.get("median_enrollment"),
            )
        )

    if maturity_score is not None:
        viz.append(
            build_metric_card(
                id="maturity_score",
                title="Maturity Score",
                value=round(maturity_score * 100, 1)
                if isinstance(maturity_score, (int, float))
                else maturity_score,
                unit="%",
            )
        )

    return viz


def build_line_chart(
    *,
    id: str,
    title: str,
    items: Iterable[dict] | dict,
    x_field: str,
    y_field: str,
    description: str | None = None,
) -> dict:
    """Build a line chart visualization."""
    if isinstance(items, dict):
        data = [{x_field: k, y_field: v} for k, v in items.items()]
    else:
        data = list(items)

    viz = Visualization(
        id=id,
        vizType=VisualizationType.LINE,
        title=title,
        description=description,
        data=data,
        config=VizConfig(
            xField=x_field,
            yField=y_field,
            legend=False,
            tooltip=True,
        ),
    )
    return viz.model_dump()


def build_iqvia_visualizations(payload: dict) -> List[dict]:
    """Create a comprehensive set of visualizations from the IQVIA agent payload.
    
    This function creates:
    1. Market overview metric cards (market size, CAGR, growth)
    2. Market growth trajectory line chart  
    3. Competitor market share pie chart
    4. Market insights text block
    5. Statista infographics as images
    """
    viz: List[dict] = []

    market_data = payload.get("market_data", {}) if payload else {}
    cagr_analysis = payload.get("cagr_analysis", {}) if payload else {}
    infographics = payload.get("infographics", []) if payload else []
    input_data = payload.get("input", {}) if payload else {}

    # Extract data structure from the nested market_data response
    data_section = market_data.get("data", {}) if market_data else {}

    market_forecast = data_section.get("market_forecast") or {}
    competitive_share = data_section.get("competitive_share") or {}

    forecast_data = market_forecast.get("data", [])
    competitive_data = competitive_share.get("data", [])
    
    # Helper to parse percentage strings
    def parse_share_value(share):
        if share is None:
            return 0
        if isinstance(share, (int, float)):
            return float(share)
        cleaned = str(share).replace('~', '').replace('%', '').strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0
    
    # ===== 1. KEY METRICS CARDS =====
    # Market Size Card (latest year)
    if forecast_data:
        latest_value = forecast_data[-1].get("value")
        latest_year = forecast_data[-1].get("year", "")
        if latest_value:
            viz.append(
                build_metric_card(
                    id="market_size",
                    title=f"Market Size ({latest_year})",
                    value=latest_value,
                    unit="B USD",
                )
            )
    
    # CAGR Metric Card
    if cagr_analysis and "cagr_percent" in cagr_analysis:
        cagr_val = cagr_analysis.get("cagr_percent")
        viz.append(
            build_metric_card(
                id="cagr_growth",
                title="CAGR",
                value=round(cagr_val, 1) if isinstance(cagr_val, (int, float)) else cagr_val,
                unit="%",
            )
        )

    # Total Growth Metric Card
    if cagr_analysis and "total_growth_percent" in cagr_analysis:
        total_growth = cagr_analysis.get("total_growth_percent")
        viz.append(
            build_metric_card(
                id="total_growth",
                title="Total Growth",
                value=round(total_growth, 1) if isinstance(total_growth, (int, float)) else total_growth,
                unit="%",
            )
        )
    
    # Market Leader Card (if competitive data available)
    if competitive_data:
        leader = competitive_data[0]
        viz.append(
            build_metric_card(
                id="market_leader",
                title="Market Leader",
                value=f"{leader.get('company', 'N/A')} ({leader.get('share', 'N/A')})",
            )
        )

    # ===== 2. MARKET GROWTH LINE CHART =====
    if forecast_data:
        # Build line chart data with proper formatting
        line_data = []
        for item in forecast_data:
            line_data.append({
                "year": str(item.get("year", "")),
                "value": item.get("value", 0),
            })
        
        viz.append(
            build_line_chart(
                id="market_growth_trend",
                title=market_forecast.get("title", "Market Growth Trajectory"),
                items=line_data,
                x_field="year",
                y_field="value",
                description=market_forecast.get("description", "Market size forecast showing growth trajectory over time (USD Billions)"),
            )
        )

    # ===== 3. COMPETITIVE MARKET SHARE PIE CHART =====
    if competitive_data:
        pie_data = [
            {"label": item.get("company"), "value": parse_share_value(item.get("share"))}
            for item in competitive_data
            if item and item.get("company")
        ]
        
        viz.append(
            build_pie_chart(
                id="competitive_share",
                title=competitive_share.get("title", "Competitive Market Share"),
                items=pie_data,
                label_field="label",
                value_field="value",
                description=competitive_share.get("description", "Market share distribution among key players"),
            )
        )

    # ===== 4. MARKET INSIGHTS TEXT BLOCK =====
    if forecast_data or competitive_data or cagr_analysis:
        insights = []
        
        # Generate insights from data
        if forecast_data and len(forecast_data) >= 2:
            start_val = forecast_data[0].get("value", 0)
            end_val = forecast_data[-1].get("value", 0)
            start_year = forecast_data[0].get("year", "")
            end_year = forecast_data[-1].get("year", "")
            if start_val and end_val:
                growth_pct = ((end_val - start_val) / start_val) * 100
                insights.append(f"• Market projected to grow from ${start_val}B ({start_year}) to ${end_val}B ({end_year}), representing {growth_pct:.1f}% total growth")
        
        if cagr_analysis and cagr_analysis.get("cagr_percent"):
            cagr = cagr_analysis.get("cagr_percent")
            trend = "strong" if cagr > 10 else "moderate" if cagr > 5 else "stable"
            insights.append(f"• Market shows {trend} growth trajectory with {cagr:.1f}% CAGR")
        
        if competitive_data:
            top_3 = competitive_data[:3]
            top_3_names = [c.get("company", "Unknown") for c in top_3]
            top_3_share = sum(parse_share_value(c.get("share")) for c in top_3)
            insights.append(f"• Top 3 players ({', '.join(top_3_names)}) control ~{top_3_share:.0f}% of the market")
            
            # Check market concentration
            leader_share = parse_share_value(competitive_data[0].get("share", 0))
            if leader_share > 50:
                insights.append(f"• Market is highly concentrated with dominant leader holding >{leader_share:.0f}% share")
            elif leader_share > 30:
                insights.append("• Market shows moderate concentration with opportunities for challengers")
            else:
                insights.append("• Fragmented market with significant opportunities for differentiation")
        
        if insights:
            viz.append({
                "id": "market_insights",
                "vizType": "text",
                "title": "Market Intelligence Summary",
                "data": {"text": "\n".join(insights)},
                "description": "Key insights derived from market data analysis"
            })

    # ===== 5. DETAILED DATA TABLES =====
    # Market forecast table
    if forecast_data:
        # Format values with billion notation
        formatted_rows = []
        for item in forecast_data:
            formatted_rows.append({
                "year": item.get("year"),
                "value": f"${item.get('value', 0)}B",
                "raw_value": item.get("value", 0)
            })
        
        columns = [
            {"key": "year", "label": "Year"},
            {"key": "value", "label": "Market Size"},
        ]
        viz.append(
            build_table(
                id="market_forecast_table",
                title="Market Forecast Details",
                columns=columns,
                rows=formatted_rows,
                page_size=10,
            )
        )

    # Competitive share table  
    if competitive_data:
        columns = [
            {"key": "company", "label": "Company"},
            {"key": "share", "label": "Market Share"},
        ]
        viz.append(
            build_table(
                id="competitive_share_table",
                title="Competitive Landscape Details",
                columns=columns,
                rows=competitive_data,
                page_size=10,
            )
        )

    # ===== 6. STATISTA INFOGRAPHICS =====
    for idx, infographic in enumerate(infographics[:6]):  # Limit to 6 infographics
        viz.append(
            {
                "id": f"infographic_{idx}",
                "vizType": "image",
                "title": infographic.get("title", "Market Research"),
                "description": infographic.get("subtitle") or infographic.get("description", ""),
                "data": {
                    "imageUrl": infographic.get("content"),
                    "caption": infographic.get("description", ""),
                    "sourceUrl": infographic.get("url", ""),
                    "source": "Statista",
                    "premium": infographic.get("premium", False),
                },
            }
        )

    return viz


def build_patent_visualizations(payload: dict) -> List[dict]:
    """Create a standard set of visualizations from the Patent FTO agent payload.
    
    Follows the same pattern as build_clinical_visualizations().
    Enhanced to support new FTO Risk Index (0-100) and multi-layer summaries.
    """
    viz: List[dict] = []

    if not payload:
        return viz

    fto = payload.get("fto", {})
    discovery = payload.get("discovery", {})
    verifications = payload.get("verifications", [])
    parsed_input = payload.get("input", {})

    # Extract data from FTO result (support both old and new canonical fields)
    fto_status = fto.get("ftoStatus", "CLEAR")
    fto_date = fto.get("ftoDate") or fto.get("earliestFreedomDate")  # Support both field names
    patents_found = fto.get("patentsFound", 0)
    confidence = fto.get("confidence", "LOW")  # Kept in memory but not displayed
    blocking_patents = fto.get("blockingPatents", [])
    
    # Get non-blocking patents from expandedResults (new schema) or fallback to old fields
    expanded_results = fto.get("expandedResults", {})
    non_blocking_patents = expanded_results.get("nonBlockingPatents", fto.get("nonBlockingPatents", []))
    expired_patents = expanded_results.get("expiredPatents", fto.get("expiredPatents", []))
    uncertain_patents = expanded_results.get("uncertainPatents", fto.get("uncertainPatents", []))
    
    recommended_actions = fto.get("recommendedActions", [])
    discovery = payload.get("discovery", {})
    
    # Use patentsFound from FTO result, fallback to discovery count
    if patents_found == 0:
        patents_found = discovery.get("totalFound", len(discovery.get("patents", [])))

    # ----- FTO Status Card (Title Case - no ALL CAPS) -----
    # Map canonical status to display text
    status_display = {
        "CLEAR": "Clear",
        "NEEDS_MONITORING": "Monitor",
        "AT_RISK": "At Risk",
        "BLOCKED": "Blocked",
        # Legacy mappings
        "LOW_RISK": "Low Risk",
        "MODERATE_RISK": "At Risk",
        "HIGH_RISK": "Blocked",
    }
    viz.append(
        build_metric_card(
            id="fto_status",
            title="FTO Status",
            value=status_display.get(fto_status, fto_status),
        )
    )

    # ----- Patents Found Card -----
    viz.append(
        build_metric_card(
            id="patents_found",
            title="Patents Found",
            value=patents_found,
        )
    )

    # ----- FTO Date Card (only if blocking patents exist) -----
    if fto_date:
        viz.append(
            build_metric_card(
                id="fto_date",
                title="FTO Date",
                value=fto_date,
            )
        )

    # ----- Patent Breakdown Pie Chart (2 slices: Blocking vs Non-Blocking) -----
    # Combine expired/uncertain into non-blocking category
    patent_breakdown = {}
    
    # Count patents by category
    blocking_count = len(blocking_patents) if blocking_patents else 0
    non_blocking_count = len(non_blocking_patents) if non_blocking_patents else 0
    expired_count = len(expired_patents) if expired_patents else 0
    uncertain_count = len(uncertain_patents) if uncertain_patents else 0
    
    # Combine all non-blocking categories (non-blocking + expired + uncertain)
    total_non_blocking = non_blocking_count + expired_count + uncertain_count
    
    # Build 2-slice pie chart (clean labels, tooltips show percentages)
    total_patents = blocking_count + total_non_blocking
    
    if total_patents > 0:
        if blocking_count > 0:
            patent_breakdown["Blocking"] = int(blocking_count)
        
        if total_non_blocking > 0:
            patent_breakdown["Non-Blocking"] = int(total_non_blocking)
        
        # Calculate percentages for description
        blocking_pct = round((blocking_count / total_patents) * 100, 1) if blocking_count > 0 else 0
        non_blocking_pct = round((total_non_blocking / total_patents) * 100, 1) if total_non_blocking > 0 else 0
        
        # Render pie chart with exactly 2 slices
        viz.append(
            build_pie_chart(
                id="patent_breakdown",
                title="Patent Landscape Overview",
                items=patent_breakdown,
                description=f"Analysis of {total_patents} patents: {blocking_count} blocking ({blocking_pct}%), {total_non_blocking} non-blocking ({non_blocking_pct}%)",
            )
        )

    # ----- Blocking Patents Table (Simplified: no risk numbers per design spec) -----
    if blocking_patents:
        blocking_rows = []
        for p in blocking_patents:
            # Use patentNumber or patent field (support both schemas)
            patent_num = p.get("patentNumber") or p.get("patent", "Unknown")
            
            blocking_rows.append({
                "patent": patent_num,
                "claimType": p.get("claimType", "Unknown"),
                "expiry": p.get("expiry") or p.get("expectedExpiry", "Unknown"),
                "riskBand": p.get("riskBand", "HIGH"),
                "reason": p.get("reason", "Blocks intended use"),
            })
        
        viz.append(
            build_table(
                id="blocking_patents",
                title="Blocking Patents",
                columns=[
                    {"key": "patent", "label": "Patent Number"},
                    {"key": "claimType", "label": "Claim Type"},
                    {"key": "expiry", "label": "Expiry Date"},
                    {"key": "riskBand", "label": "Risk Band"},
                    {"key": "reason", "label": "Reason"},
                ],
                rows=blocking_rows,
                description="Patents that may block freedom to operate",
            )
        )

    # NOTE: Removed "Blocking Patent Claim Types" pie chart per design spec
    # Claim type distribution is available in blockingPatentsSummary.claimTypeCounts if needed
    
    # NOTE: Non-blocking patents are kept in memory (expandedResults) but not displayed
    # They are available for export/drill-down but not shown in the main visualization

    # ----- Recommended Actions Table (Updated: reason + nextStep singular) -----
    if recommended_actions:
        action_rows = []
        for i, action in enumerate(recommended_actions):
            if isinstance(action, dict):
                # Support both "reason" (new) and "rationale" (legacy) field names
                reason = action.get("reason") or action.get("rationale", "")
                # Support both "nextStep" (new singular) and "nextSteps" (legacy array)
                next_step = action.get("nextStep", "")
                if not next_step and action.get("nextSteps"):
                    next_step = action.get("nextSteps")[0] if action.get("nextSteps") else ""
                
                action_rows.append({
                    "priority": i + 1,
                    "action": action.get("action", "Unknown"),
                    "feasibility": action.get("feasibility", "MEDIUM"),
                    "reason": reason,
                    "nextStep": next_step,
                })
            else:
                # Legacy string format
                action_rows.append({
                    "priority": i + 1,
                    "action": str(action),
                    "feasibility": "MEDIUM",
                    "reason": "",
                    "nextStep": "",
                })
        
        viz.append(
            build_table(
                id="recommended_actions",
                title="Recommended Actions",
                columns=[
                    {"key": "priority", "label": "#"},
                    {"key": "action", "label": "Action"},
                    {"key": "feasibility", "label": "Feasibility"},
                    {"key": "reason", "label": "Reason"},
                    {"key": "nextStep", "label": "Next Step"},
                ],
                rows=action_rows,
                description="Prioritized list of recommended next steps with feasibility ratings",
            )
        )

    # ----- Expired Patents Table (if any) -----
    if expired_patents:
        expired_rows = []
        for p in expired_patents:
            if isinstance(p, dict):
                expired_rows.append({
                    "patent": p.get("patent", "Unknown"),
                    "expiry": p.get("expectedExpiry", "Expired"),
                })
            else:
                expired_rows.append({"patent": str(p), "expiry": "Expired"})
        
        viz.append(
            build_table(
                id="expired_patents",
                title="Expired Patents",
                columns=[
                    {"key": "patent", "label": "Patent Number"},
                    {"key": "expiry", "label": "Expiry Date"},
                ],
                rows=expired_rows,
                description="Patents that have already expired",
            )
        )

    return viz


def build_exim_visualizations(payload: dict) -> List[dict]:
    """Create a standard set of visualizations from the EXIM agent payload."""
    viz: List[dict] = []
    
    if not payload:
        return viz
    
    input_data = payload.get("input", {})
    trade_data = payload.get("trade_data", {})
    analysis = payload.get("analysis", {})
    llm_insights = payload.get("llm_insights", {})
    
    summary = analysis.get("summary", {})
    top_partners = analysis.get("top_partners", [])
    rows = trade_data.get("rows", [])
    
    product = input_data.get("product", "Pharmaceutical")
    trade_type = input_data.get("trade_type", "export").title()
    year = input_data.get("year", "2024-25")
    hs_code = input_data.get("hs_code", "")
    data_source = payload.get("data_source", "Trade API")
    
    # NOTE: Summary description removed per design spec - too verbose
    
    # 1. Top Trading Partners Bar Chart
    if top_partners:
        partner_data = [
            {"partner": p.get("name", "Unknown")[:20], "value": p.get("current_value", 0)}
            for p in top_partners[:10]  # Top 10
        ]
        description = f"Trade values in USD Million for HS Code: {hs_code}"
        if llm_insights.get("trade_volume_description"):
            description += f"\n\n{llm_insights.get('trade_volume_description')}"
        viz.append(
            build_bar_chart(
                id="top_trading_partners",
                title=f"Top {trade_type} Partners for {product.title()} ({year})",
                description=description,
                items=partner_data,
                x_field="partner",
                y_field="value",
                orientation="horizontal",
            )
        )
    
    # NOTE: Growth Distribution Pie Chart removed per design spec
    
    # 3. Trade Data Table
    if rows:
        # Determine columns based on available data
        columns = []
        sample_row = rows[0] if rows else {}
        
        # Standard columns for EXIM data
        possible_columns = [
            {"key": "Country", "label": "Country"},
            {"key": "Commodity", "label": "Commodity"},
            {"key": "2023 - 2024", "label": "2023-24 (USD Mn)"},
            {"key": "2024 - 2025", "label": "2024-25 (USD Mn)"},
            {"key": "%Share", "label": "Market Share %"},
            {"key": "%Growth", "label": "YoY Growth %"},
        ]
        
        for col in possible_columns:
            if col["key"] in sample_row:
                columns.append(col)
        
        # If no standard columns found, use all keys
        if not columns:
            columns = [{"key": k, "label": k} for k in sample_row.keys() if k not in ['S.No.', 'HSCode']]
        
        viz.append(
            build_table(
                id="trade_data_table",
                title=f"{trade_type} Trade Data - {product.title()}",
                description=f"Detailed trade statistics for HS Code: {hs_code}. Data source: {data_source}",
                columns=columns,
                rows=rows[:20],  # Top 20 records
                page_size=15,
            )
        )
    
    # 4. Summary Metric Cards
    if summary:
        # Total Current Year Value
        total_current = summary.get("total_current_year", 0)
        if total_current:
            viz.append(
                build_metric_card(
                    id="total_trade_value",
                    title=f"Total {trade_type} Value ({year})",
                    value=round(total_current, 2),
                    unit="USD Mn",
                )
            )
        
        # YoY Growth - Use "overall_growth" field from EXIM agent (was incorrectly looking for "yoy_growth_percent")
        yoy_growth = summary.get("overall_growth", summary.get("yoy_growth_percent", 0))
        if yoy_growth is not None and yoy_growth != 0:
            # Format growth as percentage string
            growth_str = f"{yoy_growth:+.1f}%"
            viz.append(
                build_metric_card(
                    id="yoy_growth",
                    title="YoY Growth",
                    value=growth_str,
                    unit="",
                )
            )
        
        # Top Partners Count
        partners_count = summary.get("top_partners_count", 0)
        if partners_count:
            viz.append(
                build_metric_card(
                    id="partners_count",
                    title="Trading Partners Analyzed",
                    value=partners_count,
                )
            )
    
    # 5. Market Share Distribution (Top 5 vs Others)
    if top_partners:
        top_5_share = sum(p.get("share", 0) for p in top_partners[:5])
        others_share = 100 - top_5_share if top_5_share < 100 else 0
        
        share_data = [
            {"label": p.get("name", "Unknown")[:15], "value": p.get("share", 0)}
            for p in top_partners[:5]
        ]
        if others_share > 0:
            share_data.append({"label": "Others", "value": round(others_share, 2)})
        
        viz.append(
            build_pie_chart(
                id="market_share_distribution",
                title=f"Market Share Distribution - {trade_type}",
                description=f"Share of total {trade_type.lower()}s by top trading partners",
                items=share_data,
            )
        )
    
    # 6. Sourcing Insights (from LLM data)
    sourcing = llm_insights.get("sourcing_insights", {})
    if sourcing:
        primary_sources = sourcing.get("primary_sources", [])
        if primary_sources:
            # Sourcing table
            sourcing_rows = []
            for src in primary_sources:
                sourcing_rows.append({
                    "country": src.get("country", "Unknown"),
                    "share": f"{src.get('share_percent', 0)}%",
                    "quality": src.get("quality_rating", "Medium"),
                    "risk": src.get("risk_level", "Medium"),
                })
            
            viz.append(
                build_table(
                    id="sourcing_insights_table",
                    title="Sourcing Insights - Primary Supply Sources",
                    description=sourcing.get("description", "Analysis of primary supply sources and their risk profiles"),
                    columns=[
                        {"key": "country", "label": "Country"},
                        {"key": "share", "label": "Market Share"},
                        {"key": "quality", "label": "Quality Rating"},
                        {"key": "risk", "label": "Risk Level"},
                    ],
                    rows=sourcing_rows,
                    page_size=10,
                )
            )
        
        # Supply concentration metric
        hhi = sourcing.get("hhi_index", 0)
        if hhi:
            viz.append(
                build_metric_card(
                    id="hhi_index",
                    title="Supply Concentration (HHI Index)",
                    value=round(hhi, 0),
                    unit="",
                )
            )
        
        # NOTE: Sourcing recommendation moved to bottom of visualization list
    
    # 7. Import Dependency Analysis (from LLM data)
    dependency = llm_insights.get("import_dependency", {})
    if dependency:
        critical_deps = dependency.get("critical_dependencies", [])
        if critical_deps:
            # Dependency table
            dep_rows = []
            for dep in critical_deps:
                alternatives = dep.get("alternative_sources", [])
                alt_str = ", ".join(alternatives[:3]) if alternatives else "Limited options"
                dep_rows.append({
                    "country": dep.get("country", "Unknown"),
                    "import_share": f"{dep.get('import_share', 0)}%",
                    "risk": dep.get("risk", "Medium"),
                    "alternatives": alt_str,
                })
            
            viz.append(
                build_table(
                    id="import_dependency_table",
                    title="Import Dependency Analysis",
                    description=dependency.get("description", "Critical import dependencies and supply chain risk assessment"),
                    columns=[
                        {"key": "country", "label": "Country"},
                        {"key": "import_share", "label": "Import Share"},
                        {"key": "risk", "label": "Risk Level"},
                        {"key": "alternatives", "label": "Alternative Sources"},
                    ],
                    rows=dep_rows,
                    page_size=10,
                )
            )
        
        # Dependency ratio metric
        dep_ratio = dependency.get("dependency_ratio", 0)
        if dep_ratio:
            viz.append(
                build_metric_card(
                    id="dependency_ratio",
                    title="Import Dependency Ratio",
                    value=round(dep_ratio, 1),
                    unit="%",
                )
            )
        
    # NOTE: Strategic recommendations removed per design spec
    
    # Risk assessment moved to end (after Import Dependency) with smaller font styling
    dependency = llm_insights.get("import_dependency", {})
    if dependency and dependency.get("risk_assessment"):
        viz.append({
            "id": "risk_assessment",
            "vizType": "text",
            "title": "Supply Chain Risk Assessment",
            "description": dependency.get("risk_assessment"),
            "data": {
                "content": dependency.get("risk_assessment"),
                "style": {"fontSize": "small"}
            },
        })
    
    # Sourcing recommendation at bottom with smaller font
    sourcing = llm_insights.get("sourcing_insights", {})
    if sourcing and sourcing.get("diversification_recommendation"):
        viz.append({
            "id": "sourcing_recommendation",
            "vizType": "text",
            "title": "Sourcing Strategy Recommendation",
            "description": sourcing.get("diversification_recommendation"),
            "data": {
                "content": sourcing.get("diversification_recommendation"),
                "style": {"fontSize": "small"}
            },
        })
    
    return viz
