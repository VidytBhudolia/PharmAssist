from crewai.tools import tool
import json
from pathlib import Path

from app.core.config import DATA_DIR

DATA_FILE = Path(DATA_DIR) / "internal_knowledge_data.json"


@tool("fetch_internal_knowledge")
def fetch_internal_knowledge(drug_name: str, indication: str = None) -> dict:
    """
    Retrieves internal knowledge base data including strategic insights,
    cross-indication comparisons, and risk assessments.

    Args:
        drug_name: Name of the drug or molecule (e.g., "semaglutide")
        indication: Specific indication to focus on (optional, e.g., "AUD", "general")

    Returns:
        Dictionary containing internal strategic insights, comparisons, and risk flags
    """
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        drug_key = drug_name.lower().replace(" ", "_")

        # Determine which dataset to return based on indication
        if indication and "aud" in indication.lower():
            key = f"{drug_key}_aud"
        else:
            key = f"{drug_key}_general"

        if key in data:
            return {
                "drug_name": drug_name,
                "indication": indication or "general",
                "data": data[key],
                "data_source": "Internal Knowledge Base",
                "note": "Data retrieved from internal strategic documents and research archives.",
            }
        else:
            return {
                "drug_name": drug_name,
                "indication": indication,
                "data": None,
                "error": f"No internal knowledge data available for {drug_name}",
                "data_source": "Internal Knowledge Base",
            }
    except FileNotFoundError:
        return {
            "error": "Internal knowledge data file not found",
            "drug_name": drug_name,
        }
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse internal knowledge data",
            "drug_name": drug_name,
        }
