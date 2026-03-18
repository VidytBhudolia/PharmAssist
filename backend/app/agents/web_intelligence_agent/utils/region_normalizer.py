"""Region name normalization utilities for Web Intelligence Agent."""

from typing import Optional

# Mapping of common region names/codes to ISO 3166-1 alpha-2 codes
REGION_MAP = {
    # Common names
    "united states": "US",
    "usa": "US",
    "america": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "india": "IN",
    "china": "CN",
    "japan": "JP",
    "germany": "DE",
    "france": "FR",
    "canada": "CA",
    "australia": "AU",
    "brazil": "BR",
    "mexico": "MX",
    "spain": "ES",
    "italy": "IT",
    "south korea": "KR",
    "korea": "KR",
    "russia": "RU",
    "netherlands": "NL",
    "switzerland": "CH",
    "sweden": "SE",
    "belgium": "BE",
    "poland": "PL",
    "austria": "AT",
    "denmark": "DK",
    "norway": "NO",
    "finland": "FI",
    "ireland": "IE",
    "portugal": "PT",
    "greece": "GR",
    "czech republic": "CZ",
    "romania": "RO",
    "hungary": "HU",
    "turkey": "TR",
    "israel": "IL",
    "south africa": "ZA",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "singapore": "SG",
    "malaysia": "MY",
    "thailand": "TH",
    "indonesia": "ID",
    "philippines": "PH",
    "vietnam": "VN",
    "new zealand": "NZ",
    "global": "GLOBAL",
    "worldwide": "GLOBAL",
    "world": "GLOBAL",
    # ISO codes (already normalized)
    "us": "US",
    "gb": "GB",
    "in": "IN",
    "cn": "CN",
    "jp": "JP",
    "de": "DE",
    "fr": "FR",
    "ca": "CA",
    "au": "AU",
    "br": "BR",
    "mx": "MX",
    "es": "ES",
    "it": "IT",
    "kr": "KR",
    "ru": "RU",
    "nl": "NL",
    "ch": "CH",
    "se": "SE",
    "be": "BE",
    "pl": "PL",
    "at": "AT",
    "dk": "DK",
    "no": "NO",
    "fi": "FI",
    "ie": "IE",
    "pt": "PT",
    "gr": "GR",
    "cz": "CZ",
    "ro": "RO",
    "hu": "HU",
    "tr": "TR",
    "il": "IL",
    "za": "ZA",
    "ar": "AR",
    "cl": "CL",
    "co": "CO",
    "sg": "SG",
    "my": "MY",
    "th": "TH",
    "id": "ID",
    "ph": "PH",
    "vn": "VN",
    "nz": "NZ",
}


def normalize_region(region: str) -> Optional[str]:
    """
    Normalize region name to ISO 3166-1 alpha-2 code.
    
    Args:
        region: Region name or code (e.g., "India", "US", "United Kingdom")
        
    Returns:
        ISO 3166-1 alpha-2 code (e.g., "IN", "US", "GB") or "GLOBAL", or None if not found
    """
    if not region or not isinstance(region, str):
        return None
    
    region_lower = region.strip().lower()
    return REGION_MAP.get(region_lower)


def is_global_region(region: Optional[str]) -> bool:
    """Check if region is global/worldwide."""
    if not region:
        return True
    return region.upper() == "GLOBAL"
