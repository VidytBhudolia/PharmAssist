from __future__ import annotations

import json

from crewai import Agent, LLM

from app.services.viz_builder import build_clinical_visualizations
from app.services.agent_scorer import score_clinical
from .tools.analyze_trial_phases import analyze_trial_phases
from .tools.fetch_clinical_trials import fetch_clinical_trials

llm = LLM(model="groq/llama-3.3-70b-versatile", max_tokens=400)

clinical_agent = Agent(
    role="Clinical Trials Agent",
    goal="Analyze clinical trial pipelines from ClinicalTrials.gov and WHO ICTRP databases",
    backstory="""
    You are an expert clinical trials intelligence analyst specializing in pharma pipeline analysis.
    
    RESPONSIBILITIES
    - Analyze active clinical trial portfolios
    - Track trial phases and sponsor activity
    - Assess pipeline maturity and competitive landscape
    - Identify emerging therapeutic approaches
    
    HARD RULES (DO NOT VIOLATE)
    - NEVER invent trial identifiers (NCT IDs), sponsors, locations, or enrollment numbers
    - If tools are unavailable or return nothing, state: "Real clinical trial data unavailable - analysis mode only"
    - Prefer tool outputs over model guesses; clearly label every data source
    - Separate facts (from tools) vs. analysis (your reasoning); do not blur them
    - Keep timelines and phases consistent across sections
    - Be concise; avoid filler text
    
    REQUIRED OUTPUT SECTIONS
    - Active Trial Table (NCT ID, sponsor, phase, status, enrollment, location if present)
    - Phase Distribution (count by phase)
    - Sponsor Profile (top sponsors with trial counts)
    - Pipeline Maturity Assessment (stage-gate view with risks/gaps)
    - Data Sources (explicitly list which tools/files were used)
    
    ERROR / NO-DATA HANDLING
    - If no trials are found: clearly say "No trials found" and provide a brief plausible next-step search suggestion
    - If partial data: return whatever is available; mark missing fields as "unknown"
    """,
    tools=[fetch_clinical_trials, analyze_trial_phases],
    verbose=True,
    allow_delegation=False,
    llm=llm,
)


def _parse_prompt(user_prompt: str) -> tuple[str | None, str | None, str | None]:
    """Deprecated: Use LLM extraction only. This function is kept for compatibility."""
    # This function is no longer used - all extraction is done via _llm_extract_prompt
    return None, None, None


def _llm_extract_prompt(
    user_prompt: str,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Use the configured LLM to extract drug, condition, phase, status from the prompt."""
    prompt = f"""You are a clinical trials data extraction expert. Your job is to extract structured information from user queries about clinical trials.

From the following query, extract EXACTLY these 4 fields:
1. drug: The name of the pharmaceutical drug or medication mentioned
2. condition: The disease, medical condition, or indication mentioned
3. phase: The clinical trial phase mentioned (e.g., 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', or 'all')
4. status: The trial status if mentioned (e.g., 'recruiting', 'ongoing', 'completed')

CRITICAL RULES:
- Extract ONLY what is explicitly stated in the query
- Do NOT make assumptions or invent information
- If a field is not mentioned, return 'null' for that field
- Drug names are typically single words or hyphenated (e.g., 'pembrolizumab', 'osimertinib')
- Conditions are typically longer phrases (e.g., 'metastatic melanoma', 'rheumatoid arthritis')
- For phase, return the exact phase mentioned, or 'all' if 'all phases' is mentioned
- Return a valid JSON object with these exact keys

User Query: {user_prompt}

Return ONLY a JSON object, nothing else:"""

    try:
        raw = llm.call(messages=[{"role": "user", "content": prompt}])
    except Exception as e:
        try:
            # Alternative: try direct string call
            raw = llm.call(prompt)
        except Exception as e2:
            print(f"[ERROR] LLM call failed: {e2}")
            return None, None, None, None

    if not isinstance(raw, str):
        raw = str(raw)

    import json as _json

    # Try to find and parse JSON from response
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        print(f"[ERROR] No JSON found in LLM response: {raw}")
        return None, None, None, None

    try:
        data = _json.loads(raw[start : end + 1])
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON from LLM: {e}")
        return None, None, None, None

    # Helper to normalize null/empty strings
    def clean_val(val):
        if val is None or (
            isinstance(val, str) and val.lower() in ("null", "none", "")
        ):
            return None
        return val

    drug = clean_val(data.get("drug"))
    condition = clean_val(data.get("condition"))
    phase = clean_val(data.get("phase"))
    status = clean_val(data.get("status"))

    print(
        f"[CLINICAL] LLM raw extracted: drug={drug}, condition={condition}, phase={phase}, status={status}"
    )

    return drug, condition, phase, status


def run_clinical_agent(
    user_prompt: str,
    *,
    drug_name: str | None = None,
    condition: str | None = None,
    phase: str | None = None,
    status: str | None = None,
) -> dict:
    """
    Run the clinical agent.

    If drug_name/condition are provided by orchestrator, use them directly.
    Otherwise, fall back to LLM extraction for backward compatibility.
    """
    print(f"[CLINICAL] Starting agent with prompt: {user_prompt}")

    # If parameters provided by orchestrator, use them directly
    if drug_name is not None or condition is not None or phase is not None or status is not None:
        print(
            f"[CLINICAL] Using orchestrator-provided params: drug={drug_name}, condition={condition}, phase={phase}, status={status}"
        )
        llm_drug = drug_name
        llm_condition = condition
        llm_phase = phase
        llm_status = status
    else:
        # Fallback to LLM extraction for backward compatibility
        print(
            "[CLINICAL] No params from orchestrator, falling back to LLM extraction..."
        )
        llm_drug, llm_condition, llm_phase, llm_status = _llm_extract_prompt(
            user_prompt
        )

    print(
        f"[CLINICAL] Final params: drug={llm_drug}, condition={llm_condition}, phase={llm_phase}, status={llm_status}"
    )

    # Prefer explicit parameters, then LLM extraction
    drug = drug_name or llm_drug
    cond = condition or llm_condition
    ph = phase or llm_phase
    stat = status or llm_status

    # Clinical trials can be searched by drug OR condition - we need at least one
    search_term = drug or cond

    if not search_term:
        return {
            "status": "error",
            "message": "Could not extract drug name or condition from query. Please provide a drug name or disease/condition.",
        }

    try:
        fetch_fn = getattr(fetch_clinical_trials, "func", fetch_clinical_trials)
        analyze_fn = getattr(analyze_trial_phases, "func", analyze_trial_phases)

        print(
            f"[CLINICAL] Fetching trials for drug={drug}, condition={cond}, phase={ph}"
        )
        trials = fetch_fn(drug_name=drug, condition=cond, phase=ph, indication=None)

        if "error" in trials:
            print(f"[CLINICAL] Error from fetch_clinical_trials: {trials.get('error')}")
            return {"status": "error", "message": trials.get("error")}

        print(f"[CLINICAL] Found {trials.get('total_trials', 0)} trials")
        analysis = analyze_fn(trials)

        # Build canonical summary object for banner
        total_trials = trials.get("total_trials", 0)
        phase_counts = analysis.get("phase_counts", {}) if analysis else {}
        phase3_count = phase_counts.get("Phase 3", 0) + phase_counts.get("PHASE3", 0)
        
        has_trials = total_trials > 0
        has_late_stage = phase3_count > 0
        
        if has_trials:
            summary_answer = "Yes" if has_late_stage else "Developing"
        else:
            summary_answer = "No"
        
        summary = {
            "researcherQuestion": "Is there clinical evidence for this drug-disease pair?",
            "answer": summary_answer,
            "explainers": []
        }
        
        if total_trials > 0:
            summary["explainers"].append(f"{total_trials} trials found")
        if phase3_count > 0:
            summary["explainers"].append(f"{phase3_count} in Phase 3")
        if analysis and analysis.get("top_sponsors"):
            top_sponsor = analysis["top_sponsors"][0] if analysis["top_sponsors"] else None
            if top_sponsor:
                summary["explainers"].append(f"Lead: {top_sponsor.get('sponsor', 'Unknown')}")

        # ── Feasibility score ──
        _clinical_score = score_clinical(
            total_trials=total_trials,
            phase_counts=phase_counts,
            top_sponsors_count=len(analysis.get("top_sponsors", [])) if analysis else 0,
        )
        summary["feasibilityScore"] = _clinical_score
        print(f"[CLINICAL] Feasibility score: {_clinical_score['score']}/100 ({_clinical_score['label']})")

        # Generate suggested next prompts
        query_term = drug or cond
        suggested_next_prompts = [
            {"prompt": f"Check patent status for {query_term}"},
            {"prompt": f"Show market size for {query_term}"},
            {"prompt": f"Find web intelligence for {query_term} safety concerns"}
        ]

        payload = {
            "summary": summary,
            "input": {
                "drug_name": drug,
                "condition": cond,
                "phase": ph,
                "status": stat,
            },
            "trials": trials,
            "analysis": analysis,
            "suggestedNextPrompts": suggested_next_prompts,
        }

        return {
            "status": "success",
            "data": payload,
            "visualizations": build_clinical_visualizations(payload),
        }
    except Exception as e:
        print(f"[CLINICAL] Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"status": "error", "message": str(e)}
