"""
Report Generator API Routes

Endpoints for generating pharmaceutical intelligence reports.
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from app.core.auth import get_current_user
from app.agents.report_generator_agent import (
    run_report_generator_agent,
    ReportGeneratorAgent,
    PharmReportTemplate,
    parse_agent_data_from_dict,
    compute_opportunity_score,
    generate_key_takeaways,
    generate_recommendation,
)

router = APIRouter(prefix="/report", tags=["Report Generator"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ReportGenerateRequest(BaseModel):
    """Request model for report generation"""
    drug_name: str = Field(..., description="Name of the drug being analyzed")
    indication: str = Field(..., description="Target disease/indication")
    agents_data: Dict[str, Any] = Field(..., description="Data from all agents")
    use_crew: bool = Field(default=False, description="Use CrewAI for enhanced analysis")
    output_format: str = Field(default="html", description="Output format: html or pdf")
    

class ReportGenerateResponse(BaseModel):
    """Response model for report generation"""
    status: str
    drug_name: str
    indication: str
    opportunity_score: Optional[float] = None
    recommendation: Optional[str] = None
    key_takeaways: Optional[List[str]] = None
    html_content: Optional[str] = None
    generated_at: str
    error: Optional[str] = None


class QuickAnalysisRequest(BaseModel):
    """Request for quick opportunity analysis without full report"""
    drug_name: str
    indication: str
    agents_data: Dict[str, Any]


class QuickAnalysisResponse(BaseModel):
    """Response for quick analysis"""
    status: str
    drug_name: str
    indication: str
    opportunity_score: float
    recommendation: str
    key_takeaways: List[str]
    data_sources: List[str]


# ============================================
# ROUTES
# ============================================

@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report(
    request: ReportGenerateRequest,
    user: dict = Depends(get_current_user),
) -> ReportGenerateResponse:
    """
    Generate a comprehensive pharmaceutical intelligence report.
    
    This endpoint aggregates data from all agents (IQVIA, Clinical, Patent, 
    EXIM, Internal Knowledge, Web Intelligence) and generates a professional
    HTML report.
    
    Args:
        request: Report generation request with drug name, indication, and agent data
        
    Returns:
        Generated report with HTML content and analysis summary
    """
    try:
        result = run_report_generator_agent(
            drug_name=request.drug_name,
            indication=request.indication,
            agents_data=request.agents_data,
            use_crew=request.use_crew,
            output_format=request.output_format,
        )
        
        return ReportGenerateResponse(
            status=result.get("status", "success"),
            drug_name=result.get("drug_name", request.drug_name),
            indication=result.get("indication", request.indication),
            opportunity_score=result.get("opportunity_score"),
            recommendation=result.get("recommendation"),
            key_takeaways=result.get("key_takeaways"),
            html_content=result.get("html_content"),
            generated_at=result.get("generated_at", datetime.now().isoformat()),
            error=result.get("error"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/html")
async def generate_html_report(
    request: ReportGenerateRequest,
    user: dict = Depends(get_current_user),
) -> Response:
    """
    Generate and return an HTML report directly.
    
    Returns the raw HTML content with proper content-type header,
    suitable for direct browser rendering or downloading.
    """
    try:
        result = run_report_generator_agent(
            drug_name=request.drug_name,
            indication=request.indication,
            agents_data=request.agents_data,
            use_crew=False,
            output_format="html",
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        html_content = result.get("html_content", "")
        
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f'inline; filename="{request.drug_name}_report.html"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/pdf")
async def generate_pdf_report(
    request: ReportGenerateRequest,
    user: dict = Depends(get_current_user),
) -> Response:
    """
    Generate and return a PDF report.
    
    Uses Playwright with Chromium for pixel-perfect PDF rendering.
    Returns the PDF file as a downloadable attachment.
    
    Requires: pip install playwright && playwright install chromium
    """
    try:
        from app.agents.report_generator_agent.tools import convert_html_to_pdf_async
        
        # First generate HTML
        result = run_report_generator_agent(
            drug_name=request.drug_name,
            indication=request.indication,
            agents_data=request.agents_data,
            use_crew=False,
            output_format="html",
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        html_content = result.get("html_content", "")
        
        # Convert to PDF using Playwright
        pdf_bytes = await convert_html_to_pdf_async(html_content)
        
        # Create safe filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in request.drug_name)
        filename = f"{safe_name}_Intelligence_Report.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except ImportError:
        raise HTTPException(
            status_code=500, 
            detail="Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-analysis", response_model=QuickAnalysisResponse)
async def quick_analysis(
    request: QuickAnalysisRequest,
    user: dict = Depends(get_current_user),
) -> QuickAnalysisResponse:
    """
    Perform quick opportunity analysis without generating full report.
    
    This is a lightweight endpoint for getting the opportunity score,
    recommendation, and key takeaways without the overhead of full
    HTML report generation.
    """
    try:
        # Parse and compute metrics
        schema = parse_agent_data_from_dict(request.agents_data)
        score = compute_opportunity_score(schema)
        takeaways = generate_key_takeaways(schema)
        recommendation = generate_recommendation(schema, score)
        
        # Track data sources
        data_sources = []
        if schema.agents_data.iqvia:
            data_sources.append("IQVIA Market Intelligence")
        if schema.agents_data.clinical:
            data_sources.append("Clinical Trials")
        if schema.agents_data.patent:
            data_sources.append("Patent Landscape")
        if schema.agents_data.exim:
            data_sources.append("EXIM Trade Data")
        if schema.agents_data.internal_knowledge:
            data_sources.append("Internal Knowledge")
        if schema.agents_data.web_intelligence:
            data_sources.append("Web Intelligence")
        
        return QuickAnalysisResponse(
            status="success",
            drug_name=request.drug_name,
            indication=request.indication,
            opportunity_score=score,
            recommendation=recommendation,
            key_takeaways=takeaways,
            data_sources=data_sources,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template/preview")
async def preview_template() -> Response:
    """
    Preview the report template with sample data.
    
    Returns an HTML preview of the report template using 
    placeholder data for development and testing purposes.
    """
    template = PharmReportTemplate()
    
    # Sample data for preview
    sample_data = {
        "drug_name": "Sample Drug",
        "indication": "Sample Indication",
        "report_date": datetime.now().strftime("%B %d, %Y"),
        "opportunity_score": 78,
        "key_takeaways": [
            "Strong market growth trajectory with 8.5% CAGR",
            "Clear freedom to operate with no blocking patents",
            "Active clinical landscape with multiple Phase II/III trials",
            "Reliable supply chain with diversified sourcing"
        ],
        "recommendation": "PROCEED: Strong commercial opportunity with manageable risk profile. Recommend initiating Phase I clinical development.",
        "iqvia": {
            "data": {
                "marketSizeUSD": 12.5,
                "cagrPercent": 8.5,
                "totalGrowthPercent": 45.2,
                "summary": {
                    "researcherQuestion": "Is this worth exploring commercially?",
                    "answer": "Yes",
                    "explainers": ["Growing market", "Strong fundamentals"]
                }
            }
        }
    }
    
    html_content = template.generate(sample_data)
    
    return Response(
        content=html_content,
        media_type="text/html"
    )
