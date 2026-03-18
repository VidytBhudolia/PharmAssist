from crewai.tools import tool
import json
from pathlib import Path

from app.core.config import DATA_DIR

DATA_FILE = Path(DATA_DIR) / "exim_data.json"


def _fetch_exim_data_impl(drug_name: str, hs_code: str = None, country: str = None) -> dict:
    """
    Internal implementation for fetching export-import trade data.

    Args:
        drug_name: Name of the drug or API (e.g., "semaglutide")
        hs_code: HS code for the product (optional)
        country: Country to focus on (optional)

    Returns:
        Dictionary containing trade volumes, price trends, and import dependency data
    """
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        drug_key = drug_name.lower().replace(" ", "_")

        if drug_key in data:
            return {
                "drug_name": drug_name,
                "hs_code": hs_code,
                "country": country,
                "data": data[drug_key],
                "data_source": "EXIM Trade Intelligence",
                "note": "Data retrieved from export-import databases. Production system uses real-time trade APIs.",
            }
        else:
            return {
                "drug_name": drug_name,
                "hs_code": hs_code,
                "country": country,
                "data": None,
                "error": f"No EXIM data available for {drug_name}",
                "data_source": "EXIM Trade Intelligence",
            }
    except FileNotFoundError:
        return {"error": "EXIM data file not found", "drug_name": drug_name}
    except json.JSONDecodeError:
        return {"error": "Failed to parse EXIM data", "drug_name": drug_name}


@tool("fetch_exim_data")
def fetch_exim_data(drug_name: str, hs_code: str = None, country: str = None) -> dict:
    """
    Fetches export-import trade data for APIs and formulations.

    Args:
        drug_name: Name of the drug or API (e.g., "semaglutide")
        hs_code: HS code for the product (optional)
        country: Country to focus on (optional)

    Returns:
        Dictionary containing trade volumes, price trends, and import dependency data
    """
    return _fetch_exim_data_impl(drug_name, hs_code, country)
