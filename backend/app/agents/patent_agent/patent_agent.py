"""
Patent FTO Analysis Agent

Purpose: Answer the critical business question:
"Can we use Drug X for Disease Y without infringing active patents?"

Architecture:
- Tool 1 (discover_patents): Find candidate patents via USPTO
- Tool 2 (verify_patent_blocking): Verify blocking status via Google Patents + LLM
- Tool 3 (fto_decision_engine): Deterministic FTO scoring and recommendations

This module follows the same pattern as clinical_agent.py for consistency.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from crewai import Agent, LLM

from app.services.viz_builder import build_patent_visualizations
from app.services.agent_scorer import score_patent
from .tools import discover_patents, verify_patent_blocking, fto_decision_engine

# LLM for prompt extraction (matches clinical_agent pattern)
llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=400)

# Agent definition (kept for backwards compatibility)
patent_agent = Agent(
    role="Pharmaceutical Patent FTO Analyst",
    goal="""
    Determine Freedom-to-Operate (FTO) for drug-disease combinations by:
    1. Discovering relevant patents from USPTO
    2. Verifying if patents block the intended use
    3. Calculating FTO risk scores and recommending actions
    
    ALWAYS answer: "Can we use Drug X for Disease Y, and if not, when can we?"
    """,
    backstory="""
    You are a pharmaceutical intellectual property analyst specializing in 
    Freedom-to-Operate (FTO) assessments for drug repurposing.
    
    HARD RULES (DO NOT VIOLATE):
    - NEVER invent patent numbers, expiry dates, or claim language
    - If tools are unavailable or return nothing, state: "Patent data unavailable"
    - Prefer tool outputs over model guesses; clearly label every data source
    - Separate facts (from tools) vs. analysis (your reasoning)
    - Jurisdiction is US unless specified otherwise
    
    REQUIRED OUTPUT:
    - FTO Status (CLEAR / LOW_RISK / MODERATE_RISK / HIGH_RISK)
    - Blocking patents with expiry dates
    - Earliest freedom date
    - Confidence level
    - Recommended actions
    """,
    tools=[discover_patents, verify_patent_blocking, fto_decision_engine],
    verbose=True,
    allow_delegation=False,
    llm=llm,
)


# ============================================================================
# INPUT PARSING (MATCHES CLINICAL AGENT PATTERN)
# ============================================================================


def _llm_extract_prompt(
    user_prompt: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Use the configured LLM to extract drug, disease, jurisdiction from the prompt.

    Follows the same pattern as clinical_agent._llm_extract_prompt()
    """
    prompt = f"""You are a pharmaceutical patent data extraction expert. Your job is to extract structured information from user queries about patent analysis and freedom-to-operate.

From the following query, extract EXACTLY these 3 fields:
1. drug: The name of the pharmaceutical drug, molecule, or compound mentioned
2. disease: The disease, medical condition, or therapeutic indication mentioned
3. jurisdiction: The patent jurisdiction if mentioned (e.g., 'US', 'EU', 'JP'). Default to 'US' if not specified.

CRITICAL RULES:
- Extract ONLY what is explicitly stated in the query
- Do NOT make assumptions or invent information
- If a field is not mentioned, return 'null' for that field (except jurisdiction defaults to 'US')
- Drug names are typically single words or hyphenated (e.g., 'metformin', 'pembrolizumab', 'aspirin')
- Diseases are typically phrases (e.g., 'diabetes', 'lung cancer', 'cardiovascular disease')
- Return a valid JSON object with these exact keys

Example queries and extractions:
- "Can we use metformin for diabetes?" -> {{"drug": "metformin", "disease": "diabetes", "jurisdiction": "US"}}
- "FTO for aspirin in pain management" -> {{"drug": "aspirin", "disease": "pain", "jurisdiction": "US"}}
- "Patent risk for atorvastatin treating cholesterol" -> {{"drug": "atorvastatin", "disease": "cholesterol", "jurisdiction": "US"}}

User Query: {user_prompt}

Return ONLY a JSON object, nothing else:"""

    try:
        raw = llm.call(messages=[{"role": "user", "content": prompt}])
    except Exception:
        try:
            # Alternative: try direct string call
            raw = llm.call(prompt)
        except Exception as e2:
            print(f"[PATENT] LLM call failed: {e2}")
            return None, None, None

    if not isinstance(raw, str):
        raw = str(raw)

    # Try to find and parse JSON from response
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        print(f"[PATENT] No JSON found in LLM response: {raw}")
        return None, None, None

    try:
        data = json.loads(raw[start : end + 1])
    except Exception as e:
        print(f"[PATENT] Failed to parse JSON from LLM: {e}")
        return None, None, None

    # Helper to normalize null/empty strings
    def clean_val(val, default=None):
        if val is None or (
            isinstance(val, str) and val.lower() in ("null", "none", "")
        ):
            return default
        return val

    drug = clean_val(data.get("drug"))
    disease = clean_val(data.get("disease"))
    jurisdiction = clean_val(data.get("jurisdiction"), default="US")

    print(
        f"[PATENT] LLM extracted: drug={drug}, disease={disease}, jurisdiction={jurisdiction}"
    )

    return drug, disease, jurisdiction


# ============================================================================
# MAIN AGENT FUNCTION (MATCHES CLINICAL AGENT PATTERN)
# ============================================================================


def run_patent_agent(
    user_prompt: str,
    *,
    drug: Optional[str] = None,
    disease: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    max_patents: int = 10,
) -> Dict[str, Any]:
    """
    Run the patent FTO agent.

    If drug/disease are provided by orchestrator, use them directly.
    Otherwise, fall back to LLM extraction for backward compatibility.

    Args:
        user_prompt: Natural language query from user
        drug: Override extracted drug name
        disease: Override extracted disease/indication
        jurisdiction: Override extracted jurisdiction (default: US)
        max_patents: Maximum patents to analyze (default: 10)

    Returns:
        Structured response matching clinical_agent output format
    """
    print(f"[PATENT] Starting agent with prompt: {user_prompt}")
    analysis_start = datetime.now()

    # -------------------------------------------------------------------------
    # STEP 1: PARSE INPUT (use orchestrator params or fallback to LLM extraction)
    # -------------------------------------------------------------------------
    if drug is not None or disease is not None or jurisdiction is not None:
        print(
            f"[PATENT] Using orchestrator-provided params: drug={drug}, disease={disease}, jurisdiction={jurisdiction}"
        )
        llm_drug = drug
        llm_disease = disease
        llm_jurisdiction = jurisdiction or "US"
    else:
        # Fallback to LLM extraction for backward compatibility
        print("[PATENT] No params from orchestrator, falling back to LLM extraction...")
        llm_drug, llm_disease, llm_jurisdiction = _llm_extract_prompt(user_prompt)

    print(
        f"[PATENT] Final params: drug={llm_drug}, disease={llm_disease}, jurisdiction={llm_jurisdiction}"
    )

    # Prefer explicit parameters, then LLM extraction
    final_drug = drug or llm_drug
    final_disease = disease or llm_disease
    final_jurisdiction = jurisdiction or llm_jurisdiction or "US"

    # Validation: need both drug and disease for patent analysis
    if not final_drug or not final_disease:
        return {
            "agentType": "PATENT_FTO",
            "status": "error",
            "query": user_prompt,
            "parsedInput": {
                "drug": final_drug,
                "disease": final_disease,
                "jurisdiction": final_jurisdiction,
            },
            "message": "Could not extract both drug name and disease/indication from query. Please specify both.",
            "metadata": {
                "analysisDate": analysis_start.isoformat(),
                "error": "MISSING_PARAMETERS",
            },
        }

    # -------------------------------------------------------------------------
    # STEP 2: TOOL PIPELINE
    # -------------------------------------------------------------------------
    try:
        # Get tool functions (handle CrewAI tool wrappers)
        discover_fn = getattr(discover_patents, "_run", discover_patents)
        verify_fn = getattr(verify_patent_blocking, "_run", verify_patent_blocking)
        fto_fn = getattr(fto_decision_engine, "_run", fto_decision_engine)

        # ----- Tool 1: Discover Patents -----
        print(
            f"[PATENT] Step 1: Discovering patents for {final_drug} + {final_disease}"
        )
        discovery_result = discover_fn(
            drug=final_drug,
            disease=final_disease,
            limit=max_patents,
        )

        patents = discovery_result.get("patents", [])
        print(f"[PATENT] Found {len(patents)} candidate patents")

        if not patents:
            # No patents found - return CLEAR status
            return _build_response(
                user_prompt=user_prompt,
                parsed_input={
                    "drug": final_drug,
                    "disease": final_disease,
                    "jurisdiction": final_jurisdiction,
                },
                fto_result={
                    "ftoStatus": "CLEAR",
                    "ftoDate": None,
                    "normalizedRiskInternal": 0,
                    "patentsFound": 0,
                    "confidence": "LOW",
                    "blockingPatentsSummary": {
                        "count": 0,
                        "claimTypeCounts": {},
                    },
                    "blockingPatents": [],
                    "expandedResults": {
                        "nonBlockingPatents": [],
                        "expiredPatents": [],
                        "uncertainPatents": [],
                    },
                    "recommendedActions": [{
                        "action": "Proceed with Standard Monitoring",
                        "reason": "No patents found; verify search parameters",
                        "feasibility": "HIGH",
                        "nextStep": "Consider expanding search terms"
                    }],
                    "summary": {
                        "executive": f"No patents found for {final_drug} in {final_disease}. FTO appears clear but recommend manual verification.",
                        "business": f"No blocking patents identified. Proceed with standard IP monitoring.",
                        "legal": "No patents analyzed. Recommend manual verification of patent landscape.",
                    },
                    "visualizationPayload": {},
                    "disclaimer": "This is an automated assessment. Consult qualified patent counsel for legal advice.",
                },
                discovery_result=discovery_result,
                verifications=[],
                analysis_start=analysis_start,
            )

        # ----- Tool 2: Verify Each Patent -----
        print(f"[PATENT] Step 2: Verifying {len(patents)} patents")
        verifications = []

        for i, patent_data in enumerate(patents):
            patent_number = patent_data.get("patentNumber")
            print(f"[PATENT]   [{i + 1}/{len(patents)}] Verifying {patent_number}")

            try:
                verification = verify_fn(
                    patent_number=patent_number,
                    drug=final_drug,
                    disease=final_disease,
                    jurisdiction=final_jurisdiction,
                )
                verifications.append(verification)
            except Exception as e:
                print(f"[PATENT]   Error verifying {patent_number}: {e}")
                verifications.append(
                    {
                        "patent": patent_number,
                        "error": str(e),
                        "blocksUse": None,
                    }
                )

        # ----- Tool 3: FTO Decision Engine -----
        print("[PATENT] Step 3: Running FTO decision engine")
        fto_result = fto_fn(
            patent_verifications=verifications,
            drug=final_drug,
            disease=final_disease,
            jurisdiction=final_jurisdiction,
            total_found_in_api=discovery_result.get("totalFound", len(patents)),
        )

        # ----- Build Response -----
        return _build_response(
            user_prompt=user_prompt,
            parsed_input={
                "drug": final_drug,
                "disease": final_disease,
                "jurisdiction": final_jurisdiction,
            },
            fto_result=fto_result,
            discovery_result=discovery_result,
            verifications=verifications,
            analysis_start=analysis_start,
        )

    except Exception as e:
        print(f"[PATENT] Pipeline error: {e}")
        import traceback

        traceback.print_exc()

        return {
            "agentType": "PATENT_FTO",
            "status": "error",
            "query": user_prompt,
            "parsedInput": {
                "drug": final_drug,
                "disease": final_disease,
                "jurisdiction": final_jurisdiction,
            },
            "message": f"Patent analysis pipeline error: {str(e)}",
            "metadata": {
                "analysisDate": analysis_start.isoformat(),
                "error": "PIPELINE_ERROR",
            },
        }


# ============================================================================
# RESPONSE BUILDER (MATCHES CLINICAL AGENT OUTPUT SHAPE)
# ============================================================================


def _build_response(
    user_prompt: str,
    parsed_input: Dict[str, Any],
    fto_result: Dict[str, Any],
    discovery_result: Dict[str, Any],
    verifications: List[Dict[str, Any]],
    analysis_start: datetime,
) -> Dict[str, Any]:
    """
    Build the final response in the canonical schema.

    CANONICAL SCHEMA (v3):
    - ftoStatus: "CLEAR" | "NEEDS_MONITORING" | "AT_RISK" | "BLOCKED"
    - ftoDate: YYYY-MM-DD (earliest freedom date) - renamed from earliestFreedomDate
    - normalizedRiskInternal: 0-100 (internal sorting only, NOT displayed)
    - patentsFound: total count
    - blockingPatentsSummary: { count, claimTypeCounts }
    - blockingPatents: compact format (no evidence, no internal scores)
    - recommendedActions: top 3 only, each with nextStep (singular)
    - expandedResults: { nonBlockingPatents, expiredPatents, uncertainPatents }
    - pieData: { labels: string[], counts: number[] } - integers only, no NaN

    Top-level keys:
    - agentType, query, parsedInput, summary, confidence
    - data (structured payload with canonical fields)
    - visualizations (from viz_builder)
    - metadata (timestamps, counts, warnings)
    """
    analysis_end = datetime.now()
    duration_ms = int((analysis_end - analysis_start).total_seconds() * 1000)

    # Extract key metrics (canonical schema)
    fto_status = fto_result.get("ftoStatus", "CLEAR")
    fto_date = fto_result.get("ftoDate")  # Renamed from earliestFreedomDate
    normalized_risk_internal = fto_result.get("normalizedRiskInternal", 0)
    patents_found = fto_result.get("patentsFound", 0)
    confidence = fto_result.get("confidence", "LOW")
    
    # Patent lists
    blocking_patents = fto_result.get("blockingPatents", [])
    blocking_patents_summary = fto_result.get("blockingPatentsSummary", {
        "count": len(blocking_patents),
        "claimTypeCounts": {},
    })
    
    # Expanded results (non-blocking patents go here)
    expanded_results = fto_result.get("expandedResults", {
        "nonBlockingPatents": [],
        "expiredPatents": [],
        "uncertainPatents": [],
    })
    
    # Recommendations (top 3 with nextStep singular)
    recommended_actions = fto_result.get("recommendedActions", [])
    
    # Summaries
    summary_obj = fto_result.get("summary", {})
    viz_payload = fto_result.get("visualizationPayload", {})

    # Build human-readable summary (use executive summary if available)
    if isinstance(summary_obj, dict):
        summary = summary_obj.get(
            "executive",
            _build_summary(
                drug=parsed_input["drug"],
                disease=parsed_input["disease"],
                fto_status=fto_status,
                num_blocking=blocking_patents_summary.get("count", len(blocking_patents)),
                fto_date=fto_date,
            ),
        )
    else:
        summary = (
            str(summary_obj)
            if summary_obj
            else _build_summary(
                drug=parsed_input["drug"],
                disease=parsed_input["disease"],
                fto_status=fto_status,
                num_blocking=blocking_patents_summary.get("count", len(blocking_patents)),
                fto_date=fto_date,
            )
        )

    # Build payload for visualizations
    payload = {
        "input": parsed_input,
        "discovery": discovery_result,
        "verifications": verifications,
        "fto": fto_result,
    }

    # Count warnings
    warnings = []
    uncertain_patents = expanded_results.get("uncertainPatents", [])
    if uncertain_patents:
        warnings.append(
            f"{len(uncertain_patents)} patent(s) could not be fully verified"
        )
    if any(p.get("hasContinuations") for p in blocking_patents):
        warnings.append(
            "Some blocking patents have continuations that may extend protection"
        )
    if fto_status == "BLOCKED":
        warnings.append(
            "BLOCKED status - immediate legal consultation recommended"
        )

    # Build canonical summary object for banner
    num_blocking = blocking_patents_summary.get("count", len(blocking_patents))
    
    if fto_status == "CLEAR":
        banner_answer = "Yes"
    elif fto_status in ("NEEDS_MONITORING", "AT_RISK"):
        banner_answer = "Risky"
    else:  # BLOCKED
        banner_answer = "No"
    
    banner_summary = {
        "researcherQuestion": "Can we proceed without patent infringement?",
        "answer": banner_answer,
        "explainers": []
    }
    
    banner_summary["explainers"].append(f"Status: {fto_status}")
    if num_blocking > 0:
        banner_summary["explainers"].append(f"{num_blocking} blocking patent(s)")
    if fto_date:
        banner_summary["explainers"].append(f"FTO date: {fto_date}")

    # ── Feasibility score ──
    non_blocking_patents = expanded_results.get("nonBlockingPatents", [])
    expired_patents = expanded_results.get("expiredPatents", [])
    _patent_score = score_patent(
        fto_status=fto_status,
        blocking_count=num_blocking,
        fto_date=fto_date,
        normalized_risk=None,
        total_patents=len(blocking_patents) + len(non_blocking_patents) + len(expired_patents),
    )
    banner_summary["feasibilityScore"] = _patent_score
    print(f"[PATENT] Feasibility score: {_patent_score['score']}/100 ({_patent_score['label']})")

    # Generate suggested next prompts
    drug = parsed_input.get("drug", "drug")
    disease = parsed_input.get("disease", "disease")
    suggested_next_prompts = [
        {"prompt": f"Show clinical trials for {drug} in {disease}"},
        {"prompt": f"Analyze market size for {drug}"},
        {"prompt": f"Find web intelligence for {drug} competitors"}
    ]

    return {
        "agentType": "PATENT_FTO",
        "status": "success",
        "query": user_prompt,
        "parsedInput": parsed_input,
        "summary": summary,
        "bannerSummary": banner_summary,  # Canonical summary for UI banner
        "confidence": confidence,
        "suggestedNextPrompts": suggested_next_prompts,
        "data": {
            # Core decision fields (canonical schema)
            "ftoStatus": fto_status,
            "ftoDate": fto_date,  # Renamed from earliestFreedomDate
            "normalizedRiskInternal": normalized_risk_internal,  # Internal use only
            "patentsFound": patents_found,
            
            # Blocking patents summary with claimTypeCounts
            "blockingPatentsSummary": blocking_patents_summary,
            
            # Blocking patents (compact format, no evidence/internal scores)
            "blockingPatents": blocking_patents,
            
            # Recommendations (top 3, each with nextStep singular)
            "recommendedActions": recommended_actions,
            
            # Multi-layer summaries
            "summaryLayers": summary_obj
            if isinstance(summary_obj, dict)
            else {
                "executive": summary,
                "business": summary,
                "legal": "Consult qualified patent counsel for detailed legal analysis.",
            },
            
            # Visualization payload (includes pieData with integer counts)
            "visualizationPayload": viz_payload,
            
            # Expanded results (non-blocking patents, expired, uncertain)
            "expandedResults": expanded_results,
            
            # Continuation warnings (kept for legal review)
            "continuationWarnings": fto_result.get("continuationWarnings", []),
            
            # Metadata
            "disclaimer": fto_result.get(
                "disclaimer",
                "This is an automated assessment. Consult qualified patent counsel for legal advice.",
            ),
        },
        "visualizations": build_patent_visualizations(payload),
        "metadata": {
            "analysisDate": analysis_start.isoformat(),
            "completedAt": analysis_end.isoformat(),
            "durationMs": duration_ms,
            "jurisdiction": parsed_input["jurisdiction"],
            "patentsDiscovered": len(discovery_result.get("patents", [])),
            "patentsVerified": len(verifications),
            "patentsBlocking": blocking_patents_summary.get("count", len(blocking_patents)),
            "patentsNonBlocking": len(expanded_results.get("nonBlockingPatents", [])),
            "patentsExpired": len(expanded_results.get("expiredPatents", [])),
            "patentsUncertain": len(expanded_results.get("uncertainPatents", [])),
            "ftoStatus": fto_status,
            "warnings": warnings,
        },
    }


def _build_summary(
    drug: str,
    disease: str,
    fto_status: str,
    num_blocking: int,
    fto_date: Optional[str],
) -> str:
    """Build a human-readable summary of the FTO analysis."""

    status_descriptions = {
        "CLEAR": f"No blocking patents identified for {drug} in {disease}. Freedom to operate appears clear.",
        "NEEDS_MONITORING": f"Minor patent risks identified for {drug} in {disease}. Proceed with caution and monitor patent landscape.",
        "AT_RISK": f"Moderate patent risks for {drug} in {disease}. {num_blocking} blocking patent(s) identified. Recommend consulting patent counsel.",
        "BLOCKED": f"High patent risk for {drug} in {disease}. {num_blocking} blocking patent(s) create significant barriers. Licensing likely required.",
    }

    summary = status_descriptions.get(
        fto_status, f"Patent analysis completed for {drug} in {disease}."
    )

    if fto_date and fto_status in ("AT_RISK", "BLOCKED"):
        summary += f" Earliest FTO date: {fto_date}."

    return summary


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["patent_agent", "run_patent_agent"]
