"""
Report Generator Agent Package

Generates comprehensive pharmaceutical intelligence reports by aggregating
data from all other agents (IQVIA, Clinical, Patent, EXIM, Internal Knowledge, Web Intelligence).

Components:
- report_generator_agent: Main CrewAI agent for report orchestration
- report_schema: Data schemas for all agent data types
- report_template: HTML/PDF template generation

Usage:
    from app.agents.report_generator_agent import run_report_generator_agent
    
    result = run_report_generator_agent(
        drug_name="Metformin",
        indication="Pancreatic Cancer",
        agents_data={
            "iqvia": {...},
            "clinical": {...},
            "patent": {...},
            "exim": {...},
            "internal_knowledge": {...},
            "web_intelligence": {...}
        }
    )
"""

from .report_generator_agent import (
    run_report_generator_agent,
    ReportGeneratorAgent,
)
from .report_schema import (
    PharmReportSchema,
    AgentDataSchema,
    IQVIAAgentData,
    ClinicalAgentData,
    PatentAgentData,
    EXIMAgentData,
    InternalKnowledgeAgentData,
    WebIntelligenceAgentData,
    parse_agent_data_from_dict,
    compute_opportunity_score,
    generate_key_takeaways,
    generate_recommendation,
)
from .report_template import PharmReportTemplate

__all__ = [
    # Main entry point
    "run_report_generator_agent",
    "ReportGeneratorAgent",
    # Schema classes
    "PharmReportSchema",
    "AgentDataSchema",
    "IQVIAAgentData",
    "ClinicalAgentData",
    "PatentAgentData",
    "EXIMAgentData",
    "InternalKnowledgeAgentData",
    "WebIntelligenceAgentData",
    # Utility functions
    "parse_agent_data_from_dict",
    "compute_opportunity_score",
    "generate_key_takeaways",
    "generate_recommendation",
    # Template
    "PharmReportTemplate",
]
