"""
Pharmaceutical Report Schema

Complete data schema for all 7 agents' data structures.
Unified schema for consistent report generation across all agent outputs.

Data Inventory from Frontend Components:
=========================================

1. IQVIA INSIGHTS AGENT:
   - market_forecast: {title, data: [{year, value}], description}
   - competitive_share: {title, data: [{company, share}]}
   - market_overview: {title, description, key_metrics}
   - summary: {researcherQuestion, answer, explainers[]}
   - marketSizeUSD: number (billions)
   - cagrPercent: number
   - totalGrowthPercent: number
   - marketLeader: {therapy, share}
   - infographics: [{title, url, source, snippet}]
   - topArticles: [{title, url, source, snippet, premium}]

2. CLINICAL TRIALS AGENT:
   - landscape_overview: {title, description}
   - phase_distribution: {title, data: [{phase, count, color}], description}
   - sponsor_profile: {title, data: [{sponsor, trial_count, focus}], description}
   - key_trials: {title, data: [{trial_id, phase, primary_endpoints, sponsor}]}
   - summary: {researcherQuestion, answer, explainers[]}

3. PATENT LANDSCAPE AGENT:
   - landscape_overview: {title, sections: [{label, value}], description}
   - filing_heatmap: {title, data: [{region, count, color}]}
   - key_patent_extract: {title, patent_number, description, risk_note}
   - ip_opportunities: {title, high_value_claims, note}
   - aud_focus: {title, sections: [{label, value}]}
   - bannerSummary: {researcherQuestion, answer, explainers[]}

4. EXIM TRADE AGENT:
   - trade_volume: {title, data: [{country, q2_2024, q3_2024, qoq_growth}]}
   - import_dependency: {title, data: [{region, dependency_percent, primary_sources, risk_level}]}
   - summary: {researcherQuestion, answer, explainers[], total_export_value, yoy_growth, trading_partners_count, supply_concentration, import_dependency_ratio}
   - visualizations: [{vizType, title, data, config}]

5. INTERNAL KNOWLEDGE AGENT:
   - strategic_synthesis: {title, insights: [{label, value}]}
   - cross_indication_comparison: {title, dimensions: [{dimension, current, current_level, new, new_level}]}
   - past_research: {title, studies: [{title, summary, findings, key_findings[]}]}
   - company_memory: {title, items: [{label, value}]}
   - documents: [{title, date, type}]
   - summary: {researcherQuestion, answer, explainers[]}

6. WEB INTELLIGENCE AGENT:
   - header: {drug, disease, region, timespan_days, granularity}
   - sentiment_summary: {positive, neutral, negative}
   - news_articles: [{title, source, publishedAt, url, snippet}]
   - forum_quotes: [{quote, site, url, sentiment}]
   - recommended_actions: []
   - confidence: "HIGH" | "MEDIUM" | "LOW"
   - summary: {researcherQuestion, answer, explainers[]}

7. REPORT GENERATOR (Status Tracking):
   - title, description
   - sections: [{title, status, color}]
   - report_file: string (path)

Chart Types Used (Recharts Library):
====================================
- BarChart (vertical & horizontal)
- PieChart (donut style)
- LineChart
- AreaChart
- DataTable (with pagination)
- MetricCard

Color Palette:
==============
PRIMARY_PALETTE = ["#003f5c", "#2f4b7c", "#665191", "#a05195", "#d45087", "#f95d6a", "#ff7c43", "#ffa600"]

Agent Colors:
- IQVIA: blue (#3b82f6)
- EXIM: teal (#14b8a6)
- Patent: amber (#f59e0b)
- Clinical: emerald (#10b981)
- Internal Knowledge: pink (#ec4899)
- Web Intelligence: cyan (#06b6d4)
- Report: violet (#8b5cf6)
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class RiskLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SentimentType(str, Enum):
    POSITIVE = "POS"
    NEGATIVE = "NEG"
    NEUTRAL = "NEU"


class TrafficLightColor(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    YELLOW = "yellow"
    RED = "red"
    BLUE = "blue"


class VisualizationType(str, Enum):
    BAR = "bar"
    PIE = "pie"
    LINE = "line"
    AREA = "area"
    TABLE = "table"
    METRIC = "metric"


# =============================================================================
# IQVIA AGENT SCHEMA
# =============================================================================

@dataclass
class MarketForecastDataPoint:
    year: str
    value: float  # USD Billions


@dataclass
class MarketForecast:
    title: str
    data: List[MarketForecastDataPoint]
    description: Optional[str] = None


@dataclass
class CompetitorShare:
    company: str
    share: str  # e.g., "20%" or "~47%"


@dataclass
class CompetitiveShareData:
    title: str
    data: List[CompetitorShare]


@dataclass
class MarketLeader:
    therapy: str
    share: str
    shareValue: Optional[float] = None


@dataclass
class MarketArticle:
    title: str
    url: str
    source: str
    snippet: Optional[str] = None
    subtitle: Optional[str] = None
    premium: bool = False


@dataclass
class IQVIASummary:
    researcherQuestion: str  # "Is this worth exploring commercially?"
    answer: str  # "Yes" / "Stable" / "No"
    explainers: List[str]


@dataclass
class IQVIAAgentData:
    """Complete IQVIA Insights Agent data structure"""
    market_forecast: Optional[MarketForecast] = None
    competitive_share: Optional[CompetitiveShareData] = None
    summary: Optional[IQVIASummary] = None
    marketSizeUSD: Optional[float] = None  # Billions
    cagrPercent: Optional[float] = None
    totalGrowthPercent: Optional[float] = None
    marketLeader: Optional[MarketLeader] = None
    infographics: List[MarketArticle] = field(default_factory=list)
    topArticles: List[MarketArticle] = field(default_factory=list)
    suggestedNextPrompts: Optional[List[Dict[str, str]]] = None
    visualizations: List[Dict] = field(default_factory=list)


# =============================================================================
# CLINICAL TRIALS AGENT SCHEMA
# =============================================================================

@dataclass
class LandscapeOverview:
    title: str
    description: str


@dataclass
class PhaseDistributionItem:
    phase: str  # "Phase I", "Phase II", "Phase III"
    count: int
    color: str  # "blue", "green", "amber"


@dataclass
class PhaseDistribution:
    title: str
    data: List[PhaseDistributionItem]
    description: Optional[str] = None


@dataclass
class SponsorProfileItem:
    sponsor: str
    trial_count: int
    focus: str


@dataclass
class SponsorProfile:
    title: str
    data: List[SponsorProfileItem]
    description: Optional[str] = None


@dataclass
class KeyTrial:
    trial_id: str  # NCT ID
    phase: str
    primary_endpoints: str
    sponsor: str


@dataclass
class KeyTrials:
    title: str
    data: List[KeyTrial]


@dataclass
class ClinicalSummary:
    researcherQuestion: str  # "Is there clinical evidence?"
    answer: str
    explainers: List[str]


@dataclass
class ClinicalAgentData:
    """Complete Clinical Trials Agent data structure"""
    landscape_overview: Optional[LandscapeOverview] = None
    phase_distribution: Optional[PhaseDistribution] = None
    sponsor_profile: Optional[SponsorProfile] = None
    key_trials: Optional[KeyTrials] = None
    summary: Optional[ClinicalSummary] = None
    suggestedNextPrompts: Optional[List[Dict[str, str]]] = None
    visualizations: List[Dict] = field(default_factory=list)


# =============================================================================
# PATENT LANDSCAPE AGENT SCHEMA
# =============================================================================

@dataclass
class LandscapeSection:
    label: str
    value: str


@dataclass
class PatentLandscapeOverview:
    title: str
    sections: List[LandscapeSection]
    description: Optional[str] = None


@dataclass
class FilingHeatmapItem:
    region: str
    count: int
    color: str  # "blue", "green", "orange", "violet"


@dataclass
class FilingHeatmap:
    title: str
    data: List[FilingHeatmapItem]


@dataclass
class KeyPatentExtract:
    title: str
    patent_number: str
    description: str
    risk_note: Optional[str] = None


@dataclass
class IPOpportunities:
    title: str
    high_value_claims: str
    note: Optional[str] = None


@dataclass
class AUDFocus:
    title: str
    sections: List[LandscapeSection]


@dataclass
class PatentSummary:
    researcherQuestion: str  # "Is there FTO risk?"
    answer: str  # "CLEAR" / "AT_RISK" / "BLOCKED"
    explainers: List[str]


@dataclass
class PatentAgentData:
    """Complete Patent Landscape Agent data structure"""
    landscape_overview: Optional[PatentLandscapeOverview] = None
    filing_heatmap: Optional[FilingHeatmap] = None
    key_patent_extract: Optional[KeyPatentExtract] = None
    ip_opportunities: Optional[IPOpportunities] = None
    aud_focus: Optional[AUDFocus] = None
    bannerSummary: Optional[PatentSummary] = None
    suggestedNextPrompts: Optional[List[Dict[str, str]]] = None
    visualizations: List[Dict] = field(default_factory=list)


# =============================================================================
# EXIM TRADE AGENT SCHEMA
# =============================================================================

@dataclass
class TradeVolumeItem:
    country: str
    q2_2024: float
    q3_2024: float
    qoq_growth: str  # "+25%"


@dataclass
class TradeVolume:
    title: str
    data: List[TradeVolumeItem]


@dataclass
class ImportDependencyItem:
    region: str
    dependency_percent: str
    primary_sources: str
    risk_level: str  # "High", "Medium", "Low"


@dataclass
class ImportDependency:
    title: str
    data: List[ImportDependencyItem]


@dataclass
class EXIMSummary:
    researcherQuestion: str  # "Can we manufacture reliably?"
    answer: str  # "Yes" / "Stable" / "At Risk"
    explainers: List[str]
    total_export_value: Optional[str] = None  # "USD Mn"
    yoy_growth: Optional[float] = None
    trading_partners_count: Optional[int] = None
    supply_concentration: Optional[float] = None  # HHI
    import_dependency_ratio: Optional[float] = None


@dataclass
class EXIMAgentData:
    """Complete EXIM Trade Agent data structure"""
    trade_volume: Optional[TradeVolume] = None
    import_dependency: Optional[ImportDependency] = None
    summary: Optional[EXIMSummary] = None
    suggestedNextPrompts: Optional[List[Dict[str, str]]] = None
    visualizations: List[Dict] = field(default_factory=list)


# =============================================================================
# INTERNAL KNOWLEDGE AGENT SCHEMA
# =============================================================================

@dataclass
class StrategicInsight:
    label: str
    value: str


@dataclass
class StrategicSynthesis:
    title: str
    insights: List[StrategicInsight]


@dataclass
class CrossIndicationDimension:
    dimension: str
    current: str
    current_level: str  # "green", "yellow", "red"
    new: str
    new_level: str


@dataclass
class CrossIndicationComparison:
    title: str
    dimensions: List[CrossIndicationDimension]


@dataclass
class PastResearchStudy:
    title: str
    summary: Optional[str] = None
    findings: Optional[str] = None
    key_findings: List[str] = field(default_factory=list)


@dataclass
class PastResearch:
    title: str
    studies: List[PastResearchStudy]


@dataclass
class CompanyMemoryItem:
    label: str
    value: str


@dataclass
class CompanyMemory:
    title: str
    items: List[CompanyMemoryItem]


@dataclass
class InternalDocument:
    title: str
    date: Optional[str] = None
    type: Optional[str] = None


@dataclass
class InternalKnowledgeSummary:
    researcherQuestion: str
    answer: str
    explainers: List[str]


@dataclass
class InternalKnowledgeAgentData:
    """Complete Internal Knowledge Agent data structure"""
    strategic_synthesis: Optional[StrategicSynthesis] = None
    cross_indication_comparison: Optional[CrossIndicationComparison] = None
    past_research: Optional[PastResearch] = None
    company_memory: Optional[CompanyMemory] = None
    documents: List[InternalDocument] = field(default_factory=list)
    summary: Optional[InternalKnowledgeSummary] = None
    suggestedNextPrompts: Optional[List[Dict[str, str]]] = None
    visualizations: List[Dict] = field(default_factory=list)


# =============================================================================
# WEB INTELLIGENCE AGENT SCHEMA
# =============================================================================

@dataclass
class WebIntelHeader:
    drug: str
    disease: str
    region: str
    timespan_days: int
    granularity: str


@dataclass
class SentimentSummary:
    positive: float  # percentage
    neutral: float
    negative: float


@dataclass
class NewsArticle:
    title: str
    source: str
    publishedAt: str
    url: str
    snippet: Optional[str] = None


@dataclass
class ForumQuote:
    quote: str
    site: str
    url: str
    sentiment: str  # "POS", "NEG", "NEU"


@dataclass
class WebIntelSummary:
    researcherQuestion: str  # "Is market sentiment favorable?"
    answer: str  # "Positive" / "Neutral" / "Negative"
    explainers: List[str]


@dataclass
class WebIntelligenceAgentData:
    """Complete Web Intelligence Agent data structure"""
    header: Optional[WebIntelHeader] = None
    sentiment_summary: Optional[SentimentSummary] = None
    news_articles: List[NewsArticle] = field(default_factory=list)
    forum_quotes: List[ForumQuote] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    summary: Optional[WebIntelSummary] = None
    suggestedNextPrompts: Optional[List[Dict[str, str]]] = None
    visualizations: List[Dict] = field(default_factory=list)


# =============================================================================
# REPORT STATUS SCHEMA
# =============================================================================

@dataclass
class ReportSection:
    title: str
    status: str  # "Complete", "In Progress", "Finalizing"
    color: str  # "green", "blue", "amber"


@dataclass
class ReportStatusData:
    """Report generation status tracking"""
    title: str
    description: str
    sections: List[ReportSection]
    report_file: Optional[str] = None


# =============================================================================
# UNIFIED AGENT DATA SCHEMA
# =============================================================================

@dataclass
class AgentDataSchema:
    """
    Unified schema containing all agent data for report generation.
    This is the master structure that the report template expects.
    """
    # Metadata
    drug_name: str
    indication: str
    report_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    session_id: Optional[str] = None
    
    # Agent Data (all optional - report handles missing data gracefully)
    iqvia: Optional[IQVIAAgentData] = None
    clinical: Optional[ClinicalAgentData] = None
    patent: Optional[PatentAgentData] = None
    exim: Optional[EXIMAgentData] = None
    internal_knowledge: Optional[InternalKnowledgeAgentData] = None
    web_intelligence: Optional[WebIntelligenceAgentData] = None
    report_status: Optional[ReportStatusData] = None
    
    # Aggregated metrics for executive summary
    opportunity_score: Optional[float] = None  # 0-100
    recommendation: Optional[str] = None
    key_takeaways: List[str] = field(default_factory=list)


# =============================================================================
# VISUALIZATION SCHEMA (for chart rendering)
# =============================================================================

@dataclass
class VizConfig:
    xField: Optional[str] = None
    yField: Optional[str] = None
    yFields: Optional[List[str]] = None
    labelField: Optional[str] = None
    valueField: Optional[str] = None
    orientation: str = "vertical"  # "vertical" | "horizontal"
    legend: bool = True
    tooltip: bool = True
    pageSize: int = 20


@dataclass
class TableColumn:
    key: str
    label: str
    type: str = "text"  # "text" | "number" | "currency" | "percent" | "status"


@dataclass
class TableData:
    columns: List[TableColumn]
    rows: List[Dict[str, Any]]


@dataclass
class VisualizationSchema:
    """Schema for visualization objects that can be embedded in reports"""
    id: str
    vizType: VisualizationType
    title: str
    description: Optional[str] = None
    data: Union[List[Dict], TableData, Dict] = field(default_factory=list)
    config: VizConfig = field(default_factory=VizConfig)


# =============================================================================
# COMPLETE REPORT SCHEMA
# =============================================================================

@dataclass
class PharmReportSchema:
    """
    Complete pharmaceutical intelligence report schema.
    
    Sections (in order):
    1. Cover Page
    2. Executive Summary
    3. Market Intelligence (IQVIA)
    4. Clinical Landscape
    5. IP & Patent Analysis
    6. Trade & Supply Chain (EXIM)
    7. Internal Knowledge
    8. External Intelligence (Web)
    9. Strategic Recommendations
    10. Appendix
    """
    
    # Report metadata
    report_id: str
    drug_name: str
    indication: str
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generated_by: str = "PharmAssist Intelligence Platform"
    version: str = "1.0"
    
    # All agent data
    agents_data: AgentDataSchema = None
    
    # Executive summary (computed from agent data)
    executive_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Strategic recommendations (computed from agent data)
    strategic_recommendations: Dict[str, Any] = field(default_factory=dict)
    
    # Visualizations array for all charts
    visualizations: List[VisualizationSchema] = field(default_factory=list)
    
    # Output paths
    pdf_path: Optional[str] = None
    html_path: Optional[str] = None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def parse_agent_data_from_dict(data: Dict[str, Any]) -> AgentDataSchema:
    """
    Parse raw agent data dictionary into structured AgentDataSchema.
    Handles nested data, missing fields, and various data formats.
    """
    drug_name = data.get("drug_name", data.get("drug", "Unknown Drug"))
    indication = data.get("indication", data.get("disease", "Unknown Indication"))
    
    schema = AgentDataSchema(
        drug_name=drug_name,
        indication=indication,
        session_id=data.get("session_id")
    )
    
    # Parse IQVIA data
    iqvia_raw = data.get("iqvia") or data.get("IQVIA_AGENT", {})
    if iqvia_raw:
        actual_data = iqvia_raw.get("data", iqvia_raw)
        schema.iqvia = IQVIAAgentData(
            marketSizeUSD=actual_data.get("marketSizeUSD"),
            cagrPercent=actual_data.get("cagrPercent"),
            totalGrowthPercent=actual_data.get("totalGrowthPercent"),
            visualizations=actual_data.get("visualizations", [])
        )
        
        # Parse market forecast
        if actual_data.get("market_forecast"):
            mf = actual_data["market_forecast"]
            schema.iqvia.market_forecast = MarketForecast(
                title=mf.get("title", "Market Forecast"),
                data=[MarketForecastDataPoint(d["year"], d["value"]) for d in mf.get("data", [])],
                description=mf.get("description")
            )
        
        # Parse competitive share
        if actual_data.get("competitive_share"):
            cs = actual_data["competitive_share"]
            schema.iqvia.competitive_share = CompetitiveShareData(
                title=cs.get("title", "Competitive Share"),
                data=[CompetitorShare(d["company"], d["share"]) for d in cs.get("data", [])]
            )
    
    # Parse Clinical data
    clinical_raw = data.get("clinical") or data.get("CLINICAL_AGENT", {})
    if clinical_raw:
        actual_data = clinical_raw.get("data", clinical_raw)
        schema.clinical = ClinicalAgentData(visualizations=actual_data.get("visualizations", []))
        
        # Handle actual clinical agent data structure
        if actual_data.get("analysis"):
            analysis = actual_data["analysis"]
            # Create landscape overview from summary
            if actual_data.get("summary"):
                summary = actual_data["summary"]
                schema.clinical.landscape_overview = LandscapeOverview(
                    title="Clinical Evidence Overview",
                    description=f"{summary.get('answer', 'Unknown')}: {', '.join(summary.get('explainers', []))}"
                )
            
            # Create phase distribution from analysis data
            if analysis.get("phase_distribution"):
                pd_data = analysis["phase_distribution"]
                phase_items = []
                for phase, count in pd_data.items():
                    phase_items.append(PhaseDistributionItem(phase, count, "blue"))
                
                schema.clinical.phase_distribution = PhaseDistribution(
                    title="Clinical Trial Phase Distribution",
                    data=phase_items,
                    description=f"Total trials analyzed: {analysis.get('total_trials', 0)}"
                )
        
        # Handle trials data for sponsor profile
        if actual_data.get("trials") and isinstance(actual_data["trials"], dict):
            trials_data = actual_data["trials"]
            if trials_data.get("trials") and isinstance(trials_data["trials"], list):
                # Extract sponsors from trial data
                sponsors = {}
                for trial in trials_data["trials"][:10]:  # First 10 trials
                    sponsor = trial.get("sponsor", "Unknown")
                    sponsors[sponsor] = sponsors.get(sponsor, 0) + 1
                
                sponsor_items = []
                for sponsor, count in list(sponsors.items())[:5]:  # Top 5 sponsors
                    sponsor_items.append(SponsorProfileItem(sponsor, count, "Clinical Research"))
                
                if sponsor_items:
                    schema.clinical.sponsor_profile = SponsorProfile(
                        title="Leading Clinical Trial Sponsors",
                        data=sponsor_items,
                        description="Top sponsors conducting clinical trials for this indication"
                    )
    
    # Parse Patent data
    patent_raw = data.get("patent") or data.get("PATENT_AGENT", {})
    if patent_raw:
        actual_data = patent_raw.get("data", patent_raw)
        schema.patent = PatentAgentData(visualizations=actual_data.get("visualizations", []))
        
        # Handle actual patent agent data structure
        if actual_data:
            # Create landscape overview from patent analysis
            sections = []
            sections.append(LandscapeSection("FTO Status", actual_data.get("ftoStatus", "Unknown")))
            sections.append(LandscapeSection("Patents Found", str(actual_data.get("patentsFound", 0))))
            sections.append(LandscapeSection("Risk Level", actual_data.get("normalizedRiskInternal", "Unknown")))
            
            # Add blocking patents summary
            blocking_summary = actual_data.get("blockingPatentsSummary", {})
            if blocking_summary:
                sections.append(LandscapeSection("Blocking Patents", str(blocking_summary.get("count", 0))))
            
            schema.patent.landscape_overview = PatentLandscapeOverview(
                title="Patent Landscape Analysis",
                sections=sections,
                description=actual_data.get("disclaimer", "Patent landscape analysis completed")
            )
        
        # Create filing heatmap from available data (if blocking patents exist)
        blocking_patents = actual_data.get("blockingPatents", [])
        if blocking_patents:
            # Group patents by region/jurisdiction
            regions = {}
            for patent in blocking_patents:
                jurisdiction = patent.get("jurisdiction", "Unknown")
                regions[jurisdiction] = regions.get(jurisdiction, 0) + 1
            
            if regions:
                heatmap_items = []
                for region, count in regions.items():
                    heatmap_items.append(FilingHeatmapItem(region, count, "red"))
                
                schema.patent.filing_heatmap = FilingHeatmap(
                    title="Patent Filing Distribution",
                    data=heatmap_items
                )
    
    # Parse EXIM data
    exim_raw = data.get("exim") or data.get("EXIM_AGENT", {})
    if exim_raw:
        actual_data = exim_raw.get("data", exim_raw)
        schema.exim = EXIMAgentData(visualizations=actual_data.get("visualizations", []))
        
        # Handle actual EXIM agent data structure
        if actual_data.get("trade_data"):
            trade_data = actual_data["trade_data"]
            rows = trade_data.get("rows", [])
            
            # Create trade volume from rows data
            if rows:
                trade_items = []
                for row in rows[:10]:  # Top 10 countries
                    country = row.get("Country", "Unknown")
                    current_val = float(row.get("2024 - 2025", "0").replace(",", "") or 0)
                    previous_val = float(row.get("2023 - 2024", "0").replace(",", "") or 0)
                    growth = row.get("%Growth", "0%")
                    
                    trade_items.append(TradeVolumeItem(country, previous_val, current_val, growth))
                
                schema.exim.trade_volume = TradeVolume(
                    title="Global Trade Volume Analysis",
                    data=trade_items
                )
        
        # Create import dependency from analysis data
        if actual_data.get("analysis"):
            analysis = actual_data["analysis"]
            summary = analysis.get("summary", {})
            
            # Use top partners data if available
            if summary.get("top_partner"):
                dependency_items = []
                top_partner = summary["top_partner"]
                total_value = summary.get("total_current_year", 0)
                
                dependency_items.append(ImportDependencyItem(
                    top_partner,
                    30.0,  # Placeholder percentage
                    [top_partner],
                    "MEDIUM"
                ))
                
                schema.exim.import_dependency = ImportDependency(
                    title="Trade Dependency Analysis",
                    data=dependency_items
                )
    
    # Parse Internal Knowledge data
    internal_raw = data.get("internal_knowledge") or data.get("INTERNAL_KNOWLEDGE_AGENT", {})
    if internal_raw:
        actual_data = internal_raw.get("data", internal_raw)
        schema.internal_knowledge = InternalKnowledgeAgentData(visualizations=actual_data.get("visualizations", []))
        
        # Handle actual internal knowledge agent data structure
        if actual_data:
            # Create strategic synthesis from available data
            insights = []
            if actual_data.get("source"):
                insights.append(StrategicInsight("Data Source", actual_data["source"]))
            if actual_data.get("file_type"):
                insights.append(StrategicInsight("File Type", actual_data["file_type"]))
            
            # Add analysis insights if available
            if actual_data.get("analysis"):
                analysis = actual_data["analysis"]
                if isinstance(analysis, dict):
                    for key, value in list(analysis.items())[:3]:  # First 3 analysis points
                        insights.append(StrategicInsight(key.replace("_", " ").title(), str(value)[:100]))
            
            if insights:
                schema.internal_knowledge.strategic_synthesis = StrategicSynthesis(
                    title="Internal Knowledge Synthesis",
                    insights=insights
                )
        
        # Create cross-indication comparison if overview data exists
        if actual_data.get("overview"):
            overview = actual_data["overview"]
            if isinstance(overview, dict):
                dimensions = []
                for key, value in list(overview.items())[:5]:  # Top 5 overview items
                    dimensions.append(CrossIndicationDimension(
                        key.replace("_", " ").title(),
                        "Current State",
                        "MEDIUM", 
                        str(value)[:50],
                        "HIGH"
                    ))
                
                if dimensions:
                    schema.internal_knowledge.cross_indication_comparison = CrossIndicationComparison(
                        title="Knowledge Cross-Reference",
                        dimensions=dimensions
                    )
    
    # Parse Web Intelligence data
    web_raw = data.get("web_intelligence") or data.get("WEB_INTELLIGENCE_AGENT", {})
    if web_raw:
        actual_data = web_raw.get("data", web_raw)
        schema.web_intelligence = WebIntelligenceAgentData(visualizations=actual_data.get("visualizations", []))
        
        # Handle actual web intelligence agent data structure
        if actual_data:
            # Create sentiment summary if available
            top_signal = actual_data.get("top_signal", {})
            if isinstance(top_signal, dict) and top_signal.get("score"):
                # Derive sentiment from signal score
                score = int(top_signal.get("score", 0))
                if score >= 70:
                    positive, neutral, negative = 80, 15, 5
                elif score >= 40:
                    positive, neutral, negative = 40, 50, 10
                else:
                    positive, neutral, negative = 20, 30, 50
                
                schema.web_intelligence.sentiment_summary = SentimentSummary(
                    positive=positive,
                    neutral=neutral, 
                    negative=negative
                )
        
        # Parse news articles from top_headlines
        headlines = actual_data.get("top_headlines", [])
        if headlines and isinstance(headlines, list):
            news_articles = []
            for headline in headlines[:5]:  # Top 5 headlines
                if isinstance(headline, dict):
                    news_articles.append(NewsArticle(
                        headline.get("title", ""),
                        headline.get("source", "Web"),
                        headline.get("publishedAt", ""),
                        headline.get("url", ""),
                        headline.get("snippet", "")
                    ))
            schema.web_intelligence.news_articles = news_articles
        
        # Parse forum quotes if available
        # Note: Our web intelligence agent doesn't return forums, but we can use headlines as proxy
        if headlines:
            forum_quotes = []
            for headline in headlines[2:4]:  # Use 2-3 headlines as forum-like quotes
                if isinstance(headline, dict):
                    forum_quotes.append(ForumQuote(
                        headline.get("snippet", headline.get("title", ""))[:200],
                        "Web Forum",
                        headline.get("url", ""),
                        "NEUTRAL"
                    ))
            schema.web_intelligence.forum_quotes = forum_quotes
        
        # Set recommended actions from analysis
        schema.web_intelligence.recommended_actions = [
            "Monitor web sentiment trends",
            "Track competitor mentions", 
            "Analyze market feedback"
        ]
        
        # Set confidence based on signal score
        if top_signal and isinstance(top_signal, dict):
            score = int(top_signal.get("score", 50))
            if score >= 70:
                confidence = "HIGH"
            elif score >= 40:
                confidence = "MEDIUM" 
            else:
                confidence = "LOW"
            schema.web_intelligence.confidence = ConfidenceLevel(confidence)
        else:
            schema.web_intelligence.confidence = ConfidenceLevel("MEDIUM")
    
    return schema


def compute_opportunity_score(schema: AgentDataSchema) -> float:
    """
    Compute an overall opportunity score (0-100) based on all agent data.
    
    Factors:
    - Market size and growth (IQVIA) - 25%
    - Clinical evidence strength (Clinical) - 25%
    - Patent freedom (Patent) - 20%
    - Supply chain reliability (EXIM) - 15%
    - Market sentiment (Web Intel) - 15%
    """
    score = 0.0
    weights_used = 0.0
    
    # IQVIA score (25%)
    if schema.iqvia:
        iqvia_score = 0
        if schema.iqvia.marketSizeUSD and schema.iqvia.marketSizeUSD > 1:
            iqvia_score += 40  # Good market size
        if schema.iqvia.cagrPercent and schema.iqvia.cagrPercent > 5:
            iqvia_score += 60  # Good growth
        score += (iqvia_score / 100) * 25
        weights_used += 25
    
    # Clinical score (25%)
    if schema.clinical and schema.clinical.phase_distribution:
        phase_data = schema.clinical.phase_distribution.data
        total_trials = sum(p.count for p in phase_data)
        late_phase = sum(p.count for p in phase_data if "II" in p.phase or "III" in p.phase)
        clinical_score = min(100, (late_phase / max(1, total_trials)) * 100 + total_trials * 5)
        score += (clinical_score / 100) * 25
        weights_used += 25
    
    # Patent score (20%)
    if schema.patent and schema.patent.bannerSummary:
        fto_answer = schema.patent.bannerSummary.answer.upper()
        if fto_answer == "CLEAR":
            score += 20
        elif fto_answer == "AT_RISK":
            score += 10
        # BLOCKED = 0
        weights_used += 20
    
    # EXIM score (15%)
    if schema.exim and schema.exim.summary:
        answer = schema.exim.summary.answer
        if answer == "Yes":
            score += 15
        elif answer == "Stable":
            score += 10
        weights_used += 15
    
    # Web Intel score (15%)
    if schema.web_intelligence and schema.web_intelligence.sentiment_summary:
        ss = schema.web_intelligence.sentiment_summary
        sentiment_score = ss.positive - ss.negative * 0.5
        score += min(15, max(0, sentiment_score * 0.15))
        weights_used += 15
    
    # Normalize to 0-100 if we don't have all data
    if weights_used > 0 and weights_used < 100:
        score = (score / weights_used) * 100
    
    return min(100, max(0, round(score, 1)))


def generate_key_takeaways(schema: AgentDataSchema) -> List[str]:
    """Generate key takeaways from all agent data"""
    takeaways = []
    
    # IQVIA takeaway
    if schema.iqvia:
        if schema.iqvia.marketSizeUSD and schema.iqvia.cagrPercent:
            size = schema.iqvia.marketSizeUSD
            cagr = schema.iqvia.cagrPercent
            takeaways.append(f"Market opportunity: ${size:.1f}B market growing at {cagr:.1f}% CAGR")
    
    # Clinical takeaway
    if schema.clinical and schema.clinical.phase_distribution:
        phases = schema.clinical.phase_distribution.data
        total = sum(p.count for p in phases)
        late = sum(p.count for p in phases if "III" in p.phase)
        takeaways.append(f"Clinical landscape: {total} active trials ({late} in Phase III)")
    
    # Patent takeaway
    if schema.patent and schema.patent.bannerSummary:
        fto = schema.patent.bannerSummary.answer
        takeaways.append(f"Freedom to operate: {fto}")
    
    # EXIM takeaway
    if schema.exim and schema.exim.trade_volume:
        countries = len(schema.exim.trade_volume.data)
        takeaways.append(f"Supply chain: Active trade with {countries} key markets")
    
    # Web Intel takeaway
    if schema.web_intelligence and schema.web_intelligence.sentiment_summary:
        ss = schema.web_intelligence.sentiment_summary
        dominant = "positive" if ss.positive > ss.negative else "mixed" if ss.positive > 30 else "cautious"
        takeaways.append(f"Market sentiment: {dominant.title()} ({ss.positive:.0f}% positive coverage)")
    
    return takeaways


def generate_recommendation(schema: AgentDataSchema, score: float) -> str:
    """Generate strategic recommendation based on opportunity score and agent data"""
    if score >= 75:
        return "STRONG OPPORTUNITY — Recommend proceeding with detailed feasibility assessment and regulatory pathway planning."
    elif score >= 50:
        return "MODERATE OPPORTUNITY — Further investigation warranted; address identified risk factors before major investment."
    elif score >= 25:
        return "LIMITED OPPORTUNITY — Significant barriers exist; consider alternative indications or formulation strategies."
    else:
        return "NOT RECOMMENDED — Current evidence does not support commercial viability; reassess with new data."
