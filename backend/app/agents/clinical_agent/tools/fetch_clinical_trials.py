from crewai.tools import tool
from app.apis.clinical_trials_api import ClinicalTrialsGovClient


@tool("fetch_clinical_trials")
def fetch_clinical_trials(
    drug_name: str = None,
    condition: str = None,
    indication: str = None,
    phase: str = None,
) -> dict:
    """
    Fetches clinical trial data from ClinicalTrials.gov v2 API for a specific drug or condition.

    Args:
        drug_name: Name of the drug or intervention (optional if condition provided)
        condition: Medical condition being studied (optional if drug_name provided)
        indication: Specific indication focus (optional, e.g., "AUD", "general") - currently unused
        phase: Trial phase filter (optional: "Phase 1", "Phase 2", "Phase 3", "Phase 4")

    Returns:
        Dictionary with normalized trials, phase distribution, and aggregates for analysis
    """
    try:
        client = ClinicalTrialsGovClient()

        # Normalize "null" string inputs to None
        if isinstance(drug_name, str) and drug_name.lower() == "null":
            drug_name = None
        if isinstance(condition, str) and condition.lower() == "null":
            condition = None
        if isinstance(phase, str) and phase.lower() == "null":
            phase = None

        # Validate at least one search term
        if not drug_name and not condition:
            return {
                "error": "At least one of drug_name or condition is required",
                "drug_name": drug_name,
                "condition": condition,
                "data_source": "ClinicalTrials.gov v2 API",
                "trials": [],
                "phase_distribution": {},
            }

        # Search trials with provided filters
        result = client.search_trials(
            drug_name=drug_name,
            condition=condition,
            phase=phase,
            page_size=200,
            max_records=300,
        )

        # Descriptive name for messages
        search_term = drug_name or condition or "unknown"

        if not result["trials"]:
            return {
                "drug_name": drug_name,
                "condition": condition,
                "phase_filter": phase,
                "error": f"No clinical trials found for {search_term}",
                "data_source": "ClinicalTrials.gov v2 API",
                "trials": [],
                "phase_distribution": {},
            }

        # Extract phase distribution in format expected by analyze_trial_phases
        phase_dist = {}
        for item in result["aggregates"]["phase_distribution"]:
            # Convert API phase names (PHASE1, PHASE2, etc.) to readable format
            phase_name = item["name"]
            if phase_name == "NA":
                phase_name = "Not Applicable"
            elif phase_name.startswith("PHASE"):
                phase_num = phase_name.replace("PHASE", "")
                phase_name = f"Phase {phase_num}"

            phase_dist[phase_name] = item["count"]

        # Prepare trial list with key fields for display
        trials_list = []
        all_interventions = set()  # Track all unique drug interventions for repurposing
        
        for trial in result["trials"]:  # Return all trials
            # Extract interventions for this trial
            trial_interventions = trial.get("interventions", [])
            for intervention in trial_interventions:
                if intervention.get("type") == "DRUG" and intervention.get("name"):
                    drug_name_lower = intervention["name"].lower()
                    # Don't add the search drug itself
                    if drug_name and drug_name.lower() != drug_name_lower:
                        all_interventions.add(intervention["name"])
            
            trials_list.append(
                {
                    "nct_id": trial.get("nct_id"),
                    "title": trial.get("brief_title"),
                    "status": trial.get("overall_status"),
                    "phase": trial.get("phase"),
                    "sponsor": trial.get("sponsors", {}).get("lead", {}).get("name"),
                    "enrollment": trial.get("enrollment", {}).get("count"),
                    "locations_count": len(trial.get("locations", [])),
                    "interventions": [i.get("name") for i in trial_interventions if i.get("type") == "DRUG"],
                }
            )

        # Identify other drugs used in the same condition (repurposing candidates)
        other_drugs_used = sorted(list(all_interventions))[:10]  # Limit to 10 most common

        return {
            "drug_name": drug_name,
            "condition": condition,
            "phase_filter": phase,
            "total_trials": result["total_returned"],
            "trials": trials_list,
            "phase_distribution": phase_dist,
            "status_distribution": {
                item["name"]: item["count"]
                for item in result["aggregates"]["status_distribution"]
            },
            "top_sponsors": [
                {"name": item["name"], "count": item["count"]}
                for item in result["aggregates"]["sponsor_counts"][:5]
            ],
            "enrollment_summary": result["aggregates"]["enrollment"],
            "other_drugs_used": other_drugs_used,  # Cross-references for repurposing
            "data_source": "ClinicalTrials.gov v2 API (Live)",
        }
    except ValueError as e:
        return {
            "error": str(e),
            "drug_name": drug_name,
            "data_source": "ClinicalTrials.gov v2 API",
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch clinical trials: {str(e)}",
            "drug_name": drug_name,
            "data_source": "ClinicalTrials.gov v2 API",
        }
