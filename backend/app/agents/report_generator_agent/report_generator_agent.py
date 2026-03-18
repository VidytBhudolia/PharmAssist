"""
Report Generator Agent

CrewAI-based agent for generating comprehensive pharmaceutical intelligence reports.
Orchestrates data collection from all agents and produces formatted HTML/PDF reports.

Features:
- Multi-agent data aggregation
- Executive summary generation
- Strategic recommendations
- HTML & PDF output support
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

# LangChain imports
from langchain_groq import ChatGroq

# Local imports
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


# Initialize LLM (using Groq like other agents)
def get_llm():
    """Get the Groq LLM instance"""
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,  # Lower temperature for structured report generation
    )


# ============================================
# TOOLS
# ============================================

@tool
def aggregate_agent_data(agent_responses: str) -> str:
    """
    Aggregates data from multiple agent responses into a unified structure.
    
    Args:
        agent_responses: JSON string containing all agent responses
        
    Returns:
        Aggregated and validated data structure
    """
    try:
        data = json.loads(agent_responses) if isinstance(agent_responses, str) else agent_responses
        
        # Parse into schema
        schema = parse_agent_data_from_dict(data)
        
        # Compute metrics
        score = compute_opportunity_score(schema)
        takeaways = generate_key_takeaways(schema)
        recommendation = generate_recommendation(schema, score)
        
        result = {
            "status": "success",
            "opportunity_score": score,
            "key_takeaways": takeaways,
            "recommendation": recommendation,
            "data_sources": [],
        }
        
        # Track which agents provided data
        if schema.agents_data.iqvia:
            result["data_sources"].append("IQVIA Market Intelligence")
        if schema.agents_data.clinical:
            result["data_sources"].append("Clinical Trials")
        if schema.agents_data.patent:
            result["data_sources"].append("Patent Landscape")
        if schema.agents_data.exim:
            result["data_sources"].append("EXIM Trade Data")
        if schema.agents_data.internal_knowledge:
            result["data_sources"].append("Internal Knowledge")
        if schema.agents_data.web_intelligence:
            result["data_sources"].append("Web Intelligence")
            
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "message": "Failed to aggregate agent data"
        })


@tool
def generate_html_report(report_data: str) -> str:
    """
    Generates an HTML report from the aggregated data.
    
    Args:
        report_data: JSON string with aggregated report data
        
    Returns:
        Path to the generated HTML file or the HTML content
    """
    try:
        data = json.loads(report_data) if isinstance(report_data, str) else report_data
        
        # Initialize template
        template = PharmReportTemplate()
        
        # Generate HTML
        html_content = template.generate(data)
        
        return json.dumps({
            "status": "success",
            "html_length": len(html_content),
            "html_content": html_content[:500] + "...",  # Preview
            "message": "HTML report generated successfully"
        })
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


@tool
def analyze_market_opportunity(iqvia_data: str, clinical_data: str) -> str:
    """
    Analyzes market opportunity by combining IQVIA market data with clinical landscape.
    
    Args:
        iqvia_data: JSON string with IQVIA market data
        clinical_data: JSON string with clinical trials data
        
    Returns:
        Market opportunity analysis
    """
    try:
        iqvia = json.loads(iqvia_data) if isinstance(iqvia_data, str) else iqvia_data
        clinical = json.loads(clinical_data) if isinstance(clinical_data, str) else clinical_data
        
        # Extract key metrics
        market_size = iqvia.get("data", {}).get("marketSizeUSD", 0)
        cagr = iqvia.get("data", {}).get("cagrPercent", 0)
        
        # Determine opportunity level
        if market_size > 10 and cagr > 8:
            opportunity = "HIGH"
            rationale = "Large market with strong growth trajectory"
        elif market_size > 5 or cagr > 5:
            opportunity = "MODERATE"
            rationale = "Growing market with potential upside"
        else:
            opportunity = "LIMITED"
            rationale = "Smaller market or slower growth expected"
            
        return json.dumps({
            "market_opportunity": opportunity,
            "market_size_usd": market_size,
            "growth_rate": cagr,
            "rationale": rationale
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def assess_ip_risk(patent_data: str) -> str:
    """
    Assesses intellectual property and freedom-to-operate risk.
    
    Args:
        patent_data: JSON string with patent landscape data
        
    Returns:
        IP risk assessment
    """
    try:
        patent = json.loads(patent_data) if isinstance(patent_data, str) else patent_data
        
        data = patent.get("data", patent)
        banner = data.get("bannerSummary", {})
        answer = banner.get("answer", "UNKNOWN")
        
        risk_map = {
            "CLEAR": {"level": "LOW", "can_proceed": True},
            "AT_RISK": {"level": "MEDIUM", "can_proceed": True},
            "BLOCKED": {"level": "HIGH", "can_proceed": False},
        }
        
        risk = risk_map.get(answer, {"level": "UNKNOWN", "can_proceed": None})
        
        return json.dumps({
            "fto_status": answer,
            "risk_level": risk["level"],
            "can_proceed": risk["can_proceed"],
            "explainers": banner.get("explainers", [])
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def evaluate_supply_chain(exim_data: str) -> str:
    """
    Evaluates supply chain reliability based on EXIM data.
    
    Args:
        exim_data: JSON string with EXIM trade data
        
    Returns:
        Supply chain evaluation
    """
    try:
        exim = json.loads(exim_data) if isinstance(exim_data, str) else exim_data
        
        data = exim.get("data", exim)
        summary = data.get("summary", {})
        
        answer = summary.get("answer", "Stable")
        
        reliability_map = {
            "Yes": "HIGH",
            "Stable": "MODERATE",
            "No": "LOW",
        }
        
        return json.dumps({
            "supply_reliability": reliability_map.get(answer, "UNKNOWN"),
            "assessment": summary.get("explainers", []),
            "trade_status": answer
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============================================
# AGENTS
# ============================================

def create_report_analyst_agent(llm) -> Agent:
    """Create the report analyst agent"""
    return Agent(
        role="Pharmaceutical Report Analyst",
        goal="Analyze all agent data and synthesize key insights for the pharmaceutical intelligence report",
        backstory="""You are a senior pharmaceutical analyst with expertise in drug repurposing 
        and market intelligence. You specialize in synthesizing complex data from multiple sources
        into actionable insights. You have deep knowledge of clinical development, IP landscape,
        market dynamics, and supply chain considerations.""",
        tools=[aggregate_agent_data, analyze_market_opportunity, assess_ip_risk, evaluate_supply_chain],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


def create_report_writer_agent(llm) -> Agent:
    """Create the report writer agent"""
    return Agent(
        role="Pharmaceutical Report Writer",
        goal="Generate professional pharmaceutical intelligence reports with clear structure and actionable recommendations",
        backstory="""You are an expert pharmaceutical report writer with years of experience 
        creating executive briefings and strategic reports. You excel at presenting complex 
        technical and market data in clear, professional formats that drive decision-making.""",
        tools=[generate_html_report],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )


# ============================================
# TASKS
# ============================================

def create_analysis_task(agent: Agent, agents_data: Dict) -> Task:
    """Create the data analysis task"""
    return Task(
        description=f"""
        Analyze the following pharmaceutical intelligence data from multiple agents:
        
        {json.dumps(agents_data, indent=2, default=str)}
        
        Your task:
        1. Aggregate data from all available agent sources (IQVIA, Clinical, Patent, EXIM, Internal, Web)
        2. Compute the overall opportunity score based on:
           - Market attractiveness (IQVIA data)
           - Clinical landscape competitiveness
           - IP/FTO risk level
           - Supply chain reliability
           - Internal strategic fit
           - Market sentiment
        3. Identify 3-5 key takeaways that a researcher would find most valuable
        4. Generate a strategic recommendation (Proceed/Proceed with Caution/Do Not Proceed)
        
        Return a structured JSON with your analysis.
        """,
        expected_output="A JSON object containing opportunity_score, key_takeaways, recommendation, and data_sources",
        agent=agent,
    )


def create_report_task(agent: Agent, drug_name: str, indication: str, analysis_result: str) -> Task:
    """Create the report generation task"""
    return Task(
        description=f"""
        Generate a professional pharmaceutical intelligence report for:
        - Drug: {drug_name}
        - Indication: {indication}
        
        Using the analysis data:
        {analysis_result}
        
        The report should include:
        1. Cover page with drug name and indication
        2. Executive summary with opportunity score and key takeaways
        3. Market Intelligence section (IQVIA data)
        4. Clinical Landscape section
        5. IP & Patent Analysis section
        6. Trade & Supply Chain section
        7. Internal Knowledge section
        8. External Intelligence section
        9. Strategic recommendations
        
        Generate the HTML report using the generate_html_report tool.
        """,
        expected_output="A confirmation that the HTML report was generated successfully with the file path",
        agent=agent,
    )


# ============================================
# MAIN FUNCTION
# ============================================

class ReportGeneratorAgent:
    """
    Main Report Generator Agent class.
    
    Orchestrates the complete report generation process from multi-agent data
    to final HTML/PDF output.
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.template = PharmReportTemplate()
        
    def generate_report(
        self,
        drug_name: str,
        indication: str,
        agents_data: Dict[str, Any],
        output_format: str = "html"
    ) -> Dict[str, Any]:
        """
        Generate a pharmaceutical intelligence report.
        
        Args:
            drug_name: Name of the drug being analyzed
            indication: Target disease/indication
            agents_data: Dictionary containing all agent responses
            output_format: Output format - "html" or "pdf"
            
        Returns:
            Dictionary with report content and metadata
        """
        try:
            # DEBUG: Save formatted data for debugging
            debug_data = {
                "drug_name": drug_name,
                "indication": indication,
                "timestamp": datetime.now().isoformat(),
                "agents_data": agents_data,
                "agents_data_keys": {k: list(v.keys()) if isinstance(v, dict) else type(v).__name__ for k, v in agents_data.items()},
            }
            
            # Save to debug folder
            from pathlib import Path
            import json
            debug_dir = Path(__file__).parent.parent.parent.parent / "debug_reports"
            debug_dir.mkdir(exist_ok=True)
            
            # Create safe filename
            safe_drug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in drug_name)
            debug_file = debug_dir / f"report_data_{safe_drug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(debug_file, 'w') as f:
                json.dump(debug_data, f, indent=2, default=str)
            
            print(f"🔍 DEBUG: Report data saved to {debug_file}")
            
            # Step 1: Parse and validate data
            print(f"  >> Step 1: Parsing and validating agent data...")
            schema = parse_agent_data_from_dict(agents_data)
            print(f"  >> Step 1: Done. Schema parsed successfully.")
            
            # Step 2: Compute metrics
            print(f"  >> Step 2: Computing metrics...")
            score = compute_opportunity_score(schema)
            takeaways = generate_key_takeaways(schema)
            recommendation = generate_recommendation(schema, score)
            print(f"  >> Step 2: Done. Score={score}, takeaways={len(takeaways)}, recommendation={recommendation[:50]}...")
            
            # Step 3: Prepare report data
            report_data = {
                "drug_name": drug_name,
                "indication": indication,
                "report_date": datetime.now().strftime("%B %d, %Y"),
                "opportunity_score": score,
                "key_takeaways": takeaways,
                "recommendation": recommendation,
                **agents_data,
            }
            
            # DEBUG: Also save the final report_data that goes to template
            template_debug_data = {
                "template_input": report_data,
                "report_keys": list(report_data.keys()),
                "template_data_summary": {
                    k: {
                        "type": type(v).__name__,
                        "keys": list(v.keys()) if isinstance(v, dict) else None,
                        "length": len(v) if isinstance(v, (list, dict, str)) else None
                    } for k, v in report_data.items()
                }
            }
            
            template_debug_file = debug_dir / f"template_input_{safe_drug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(template_debug_file, 'w') as f:
                json.dump(template_debug_data, f, indent=2, default=str)
            
            print(f"🔍 DEBUG: Template data saved to {template_debug_file}")
            
            # Step 4: Generate HTML
            print(f"  >> Step 4: Generating HTML from template...")
            html_content = self.template.generate(report_data)
            print(f"  >> Step 4: Done. HTML length={len(html_content)}")
            
            result = {
                "status": "success",
                "drug_name": drug_name,
                "indication": indication,
                "opportunity_score": score,
                "recommendation": recommendation,
                "key_takeaways": takeaways,
                "format": output_format,
                "html_content": html_content,
                "generated_at": datetime.now().isoformat(),
            }
            
            print(f"  >> ReportGeneratorAgent.generate_report: SUCCESS")
            return result
            
        except Exception as e:
            print(f"  >> ReportGeneratorAgent.generate_report: FAILED with error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "drug_name": drug_name,
                "indication": indication,
            }
    
    def generate_report_with_crew(
        self,
        drug_name: str,
        indication: str,
        agents_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate report using CrewAI multi-agent collaboration.
        
        This method uses CrewAI agents for more sophisticated analysis
        and report generation.
        
        Args:
            drug_name: Name of the drug
            indication: Target indication
            agents_data: All agent data
            
        Returns:
            Report generation result
        """
        try:
            # Create agents
            analyst = create_report_analyst_agent(self.llm)
            writer = create_report_writer_agent(self.llm)
            
            # Create analysis task
            analysis_task = create_analysis_task(analyst, agents_data)
            
            # Create crew for analysis
            analysis_crew = Crew(
                agents=[analyst],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True,
            )
            
            # Run analysis
            analysis_result = analysis_crew.kickoff()
            
            # Create report task
            report_task = create_report_task(writer, drug_name, indication, str(analysis_result))
            
            # Create crew for report generation
            report_crew = Crew(
                agents=[writer],
                tasks=[report_task],
                process=Process.sequential,
                verbose=True,
            )
            
            # Generate report
            report_result = report_crew.kickoff()
            
            # Generate final HTML using template
            report_data = {
                "drug_name": drug_name,
                "indication": indication,
                "report_date": datetime.now().strftime("%B %d, %Y"),
                **agents_data,
            }
            
            # Add analysis insights
            try:
                analysis_dict = json.loads(str(analysis_result))
                report_data.update(analysis_dict)
            except:
                pass
            
            html_content = self.template.generate(report_data)
            
            return {
                "status": "success",
                "drug_name": drug_name,
                "indication": indication,
                "html_content": html_content,
                "analysis_summary": str(analysis_result),
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "drug_name": drug_name,
                "indication": indication,
            }
    
    def generate_quick_report(
        self,
        drug_name: str,
        indication: str,
        agents_data: Dict[str, Any],
    ) -> str:
        """
        Generate a quick HTML report without CrewAI overhead.
        
        Useful for faster report generation when detailed AI analysis
        is not required.
        
        Args:
            drug_name: Name of the drug
            indication: Target indication
            agents_data: All agent data
            
        Returns:
            HTML content string
        """
        return self.template.generate_from_agents_data(agents_data, drug_name, indication)


# ============================================
# RUN FUNCTION (for integration)
# ============================================

def run_report_generator_agent(
    drug_name: str,
    indication: str,
    agents_data: Dict[str, Any],
    use_crew: bool = False,
    output_format: str = "html",
) -> Dict[str, Any]:
    """
    Main entry point for report generation.
    
    Args:
        drug_name: Name of the drug
        indication: Target indication
        agents_data: Dictionary with all agent responses
        use_crew: Whether to use CrewAI for enhanced analysis
        output_format: "html" or "pdf"
        
    Returns:
        Report generation result with HTML content
    """
    print(f"\n>>> REPORT GENERATOR: run_report_generator_agent called")
    print(f">>> REPORT GENERATOR: drug={drug_name}, indication={indication}, format={output_format}, use_crew={use_crew}")
    print(f">>> REPORT GENERATOR: agents_data keys={list(agents_data.keys())}")
    
    agent = ReportGeneratorAgent()
    
    if use_crew:
        print(f">>> REPORT GENERATOR: Using CrewAI path")
        result = agent.generate_report_with_crew(drug_name, indication, agents_data)
    else:
        print(f">>> REPORT GENERATOR: Using direct generation path")
        result = agent.generate_report(drug_name, indication, agents_data, output_format)
    
    print(f">>> REPORT GENERATOR: Result status={result.get('status')}, html_length={len(result.get('html_content', ''))}")
    if result.get('status') == 'error':
        print(f">>> REPORT GENERATOR: ERROR: {result.get('error')}")
    
    return result


# ============================================
# DIRECT EXECUTION
# ============================================

if __name__ == "__main__":
    # Test with mock data
    from pathlib import Path
    import sys
    
    # Load mock data
    mock_data_path = Path(__file__).parent.parent.parent.parent / "mockData"
    
    test_data = {}
    
    # Try to load mock data files
    mock_files = {
        "iqvia": "iqvia.json",
        "clinical": "clinical_data.json",
        "patent": "patent_data.json",
        "exim": "exim_data.json",
        "internal_knowledge": "internal_knowledge_data.json",
        "web_intelligence": "web_intel.json",
    }
    
    for key, filename in mock_files.items():
        file_path = mock_data_path / filename
        if file_path.exists():
            with open(file_path, "r") as f:
                test_data[key] = json.load(f)
    
    # Generate test report
    result = run_report_generator_agent(
        drug_name="Metformin",
        indication="Cancer (Pancreatic Ductal Adenocarcinoma)",
        agents_data=test_data,
        use_crew=False,
    )
    
    if result["status"] == "success":
        # Save HTML to file
        output_path = Path(__file__).parent / "test_report.html"
        with open(output_path, "w") as f:
            f.write(result["html_content"])
        print(f"✅ Report generated: {output_path}")
        print(f"   Opportunity Score: {result.get('opportunity_score', 'N/A')}")
        print(f"   Recommendation: {result.get('recommendation', 'N/A')}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
