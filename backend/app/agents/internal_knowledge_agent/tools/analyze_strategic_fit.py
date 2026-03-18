from crewai.tools import tool
import json
from pathlib import Path

from app.core.config import DATA_DIR

DATA_FILE = Path(DATA_DIR) / "internal_knowledge_data.json"


@tool("analyze_strategic_fit")
def analyze_strategic_fit(drug_name: str, target_indication: str) -> dict:
    """
    Analyzes the strategic fit of a drug for a specific indication based on
    internal frameworks and kill-criteria assessments.

    Args:
        drug_name: Name of the drug or molecule
        target_indication: The indication being evaluated for strategic fit

    Returns:
        Dictionary containing strategic fit assessment and recommendations
    """
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        drug_key = drug_name.lower().replace(" ", "_")

        # Check for AUD-specific data
        aud_key = f"{drug_key}_aud"
        general_key = f"{drug_key}_general"

        result = {
            "drug_name": drug_name,
            "target_indication": target_indication,
            "data_source": "Internal Strategic Framework",
        }

        if "aud" in target_indication.lower() and aud_key in data:
            aud_data = data[aud_key]
            result["strategic_assessment"] = aud_data.get("aud_focus", {})
            result["risk_assessment"] = aud_data.get("risk_flags", {})
        elif general_key in data:
            general_data = data[general_key]
            result["strategic_assessment"] = general_data.get("strategic_synthesis", {})
            result["comparison_matrix"] = general_data.get(
                "cross_indication_comparison", {}
            )
        else:
            result["error"] = f"No strategic data available for {drug_name}"

        return result

    except FileNotFoundError:
        return {
            "error": "Strategic framework data file not found",
            "drug_name": drug_name,
        }
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse strategic framework data",
            "drug_name": drug_name,
        }
