"""
FastAPI routes for EXIM Trade Analysis
Endpoints for Trade Volume, Sourcing Insights, Import Dependency
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from wits_api_client import WITSAPIClient, OutputFormatter

router = APIRouter(prefix="/api/exim", tags=["exim"])

# Pydantic models
class TradeVolumeResponse(BaseModel):
    product: str
    product_name: str
    reporter: str
    year: str
    trade_value: float
    currency: str
    status: str

class Partner(BaseModel):
    partner: str
    value: float
    share: float

class SourcingInsightsResponse(BaseModel):
    product: str
    product_name: str
    reporter: str
    year: str
    top_partners: List[Partner]
    total_imports: float
    hhi_index: float
    risk_level: str
    status: str

class Dependency(BaseModel):
    partner: str
    import_share: float
    risk: str
    recommendation: str

class ImportDependencyResponse(BaseModel):
    product: str
    product_name: str
    reporter: str
    year: str
    critical_dependencies: List[Dependency]
    moderate_dependencies: List[Dependency]
    total_high_risk: int
    concentration_ratio: float
    status: str

class CompleteReportResponse(BaseModel):
    trade_volume: dict
    sourcing_insights: dict
    import_dependency: dict
    metadata: dict


# Routes
@router.get("/trade-volume", response_model=TradeVolumeResponse)
async def get_trade_volume(
    product: str = Query("3004", description="HS code (e.g., 3004 for Medicaments)"),
    reporter: str = Query("usa", description="Country ISO3 code"),
    year: str = Query("2022", description="Year for data"),
    indicator: str = Query("XPRT-TRD-VL", description="XPRT-TRD-VL for exports, MPRT-TRD-VL for imports")
):
    """
    Get trade volume chart data
    
    Products:
    - 2935: Active Pharmaceutical Ingredients
    - 2941: Antibiotics
    - 3002: Vaccines
    - 3004: Medicaments (default)
    - 3005: Medical Supplies
    """
    data = WITSAPIClient.get_trade_volume(product, reporter, year, indicator)
    
    if data.get("status") == "failed":
        raise HTTPException(status_code=400, detail=data.get("error", "Failed to fetch trade volume"))
    
    return data


@router.get("/sourcing-insights", response_model=SourcingInsightsResponse)
async def get_sourcing_insights(
    product: str = Query("3004", description="HS code"),
    reporter: str = Query("usa", description="Country ISO3 code"),
    year: str = Query("2022", description="Year for data")
):
    """
    Get sourcing insights with supply concentration analysis
    
    Returns:
    - Top trading partners
    - HHI Index (market concentration)
    - Risk level assessment
    """
    data = WITSAPIClient.get_sourcing_insights(product, reporter, year)
    
    if data.get("status") == "failed":
        raise HTTPException(status_code=400, detail=data.get("error", "Failed to fetch sourcing insights"))
    
    return data


@router.get("/import-dependency", response_model=ImportDependencyResponse)
async def get_import_dependency(
    product: str = Query("3004", description="HS code"),
    reporter: str = Query("usa", description="Country ISO3 code"),
    year: str = Query("2022", description="Year for data"),
    threshold: float = Query(50.0, description="Dependency threshold percentage")
):
    """
    Get import dependency analysis
    
    Returns:
    - Critical dependencies (>50% import share)
    - Moderate dependencies (20-50%)
    - Risk classifications
    - Recommendations
    """
    data = WITSAPIClient.get_import_dependency(product, reporter, year, threshold)
    
    if data.get("status") == "failed":
        raise HTTPException(status_code=400, detail=data.get("error", "Failed to fetch import dependency"))
    
    return data


@router.get("/complete-report", response_model=CompleteReportResponse)
async def get_complete_report(
    product: str = Query("3004", description="HS code"),
    reporter: str = Query("usa", description="Country ISO3 code"),
    year: str = Query("2022", description="Year for data")
):
    """
    Get complete EXIM report with all three outputs:
    1. Trade volume charts
    2. Sourcing insights
    3. Import dependency analysis
    """
    report = WITSAPIClient.generate_complete_report(product, reporter, year)
    
    # Check if any component failed
    if (report.get("trade_volume", {}).get("status") == "failed" or
        report.get("sourcing_insights", {}).get("status") == "failed" or
        report.get("import_dependency", {}).get("status") == "failed"):
        raise HTTPException(status_code=400, detail="Failed to generate complete report")
    
    return report


@router.get("/metadata")
async def get_metadata():
    """
    Get metadata about available products, countries, and indicators
    """
    return {
        "products": WITSAPIClient.PHARMA_PRODUCTS,
        "countries": WITSAPIClient.COUNTRIES,
        "indicators": WITSAPIClient.INDICATORS,
        "data_source": "World Bank WITS API v1.4.1"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "api": "EXIM Trade Analysis"}
