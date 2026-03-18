"""Unified access point for all agents.

This groups existing agent packages without changing their internal structure.
"""

from clinical_agent import clinical_agent
from exim_agent import exim_agent
from iqvia_agent import iqvia_agent
from patent_agent import patent_agent
from internal_knowledge_agent import internal_knowledge_agent
from report_generator import report_generator_agent
from orchestrator_agent import orchestrator_agent
from web_intelligence_agent import web_intelligence_agent

__all__ = [
    "clinical_agent",
    "exim_agent",
    "iqvia_agent",
    "patent_agent",
    "internal_knowledge_agent",
    "report_generator_agent",
    "orchestrator_agent",
    "web_intelligence_agent",
]
