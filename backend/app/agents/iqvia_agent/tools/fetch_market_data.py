from crewai.tools import tool
import json
from pathlib import Path

from app.core.config import DATA_DIR

DATA_FILE = Path(DATA_DIR) / "iqvia_data.json"


@tool("fetch_market_data")
def fetch_market_data(
    drug_name: str,
    therapy_area: str = None,
    indication: str = None,
    region: str = "Global",
) -> dict:
    """
    Fetches pharmaceutical market data including market size, sales trends, and competitive landscape.

    Args:
        drug_name: Name of the drug or molecule, or disease/condition name (e.g., "breast cancer", "diabetes")
        therapy_area: Therapeutic area (e.g., "Oncology", "Diabetes", "Cardiovascular")
        indication: Specific indication focus (optional, e.g., "AUD", "general")
        region: Geographic region (default: "Global", options: "US", "EU", "Asia", "Global")

    Returns:
        Dictionary containing market size, CAGR, top competitors, and sales trends
    """
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Normalize the search term
        search_term = drug_name.lower().replace(" ", "_").replace("-", "_")
        
        # Try different key patterns
        possible_keys = []
        
        # 1. Direct match with indication
        if indication and "aud" in indication.lower():
            possible_keys.append(f"{search_term}_aud")
        
        # 2. Direct match with general
        possible_keys.append(f"{search_term}_general")
        
        # 3. Try therapy area mapping if provided
        if therapy_area:
            therapy_key = therapy_area.lower().replace(" ", "_")
            possible_keys.append(f"{therapy_key}_general")
        
        # 4. Try common disease/condition mappings
        disease_mappings = {
            "breast_cancer": "breast_cancer_general",
            "lung_cancer": "lung_cancer_general",
            "cancer": "oncology_general",
            "oncology": "oncology_general",
            "diabetes": "diabetes_general",
            "type_2_diabetes": "diabetes_general",
            "alzheimer": "alzheimer_general",
            "alzheimers": "alzheimer_general",
            "immunology": "immunology_general",
            "autoimmune": "immunology_general",
            "glp_1": "semaglutide_general",
            "ozempic": "semaglutide_general",
            "wegovy": "semaglutide_general",
        }
        
        if search_term in disease_mappings:
            possible_keys.insert(0, disease_mappings[search_term])
        
        # 5. Fuzzy match - look for keys containing the search term
        for key in data.keys():
            if search_term in key or any(part in key for part in search_term.split("_") if len(part) > 3):
                if key not in possible_keys:
                    possible_keys.append(key)
        
        # Find first matching key
        matched_key = None
        for key in possible_keys:
            if key in data:
                matched_key = key
                break
        
        if matched_key:
            return {
                "drug_name": drug_name,
                "therapy_area": therapy_area,
                "indication": indication or "general",
                "region": region,
                "data": data[matched_key],
                "matched_key": matched_key,
                "data_source": "IQVIA Market Intelligence",
                "note": "Data retrieved from IQVIA datasets. Production system uses real-time IQVIA API.",
            }
        else:
            # Return available keys for debugging
            return {
                "drug_name": drug_name,
                "therapy_area": therapy_area,
                "region": region,
                "data": None,
                "error": f"No IQVIA data available for {drug_name}",
                "available_datasets": list(data.keys()),
                "data_source": "IQVIA Market Intelligence",
            }
    except FileNotFoundError:
        return {"error": "IQVIA data file not found", "drug_name": drug_name}
    except json.JSONDecodeError:
        return {"error": "Failed to parse IQVIA data", "drug_name": drug_name}
