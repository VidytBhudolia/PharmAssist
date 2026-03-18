from crewai.tools import tool

@tool("analyze_trial_phases")
def analyze_trial_phases(trials_data: dict) -> dict:
    """
    Analyzes clinical trial phase distribution and provides deep pipeline maturity insights.
    
    Args:
        trials_data: Dictionary containing clinical trials information with phase data
    
    Returns:
        Dictionary with detailed phase analysis, success probabilities, pipeline insights, 
        competitive positioning, and strategic recommendations
    """
    # Industry-standard FDA approval success rates by phase
    success_rates = {
        "Phase 1": 0.63,
        "Phase 2": 0.31,
        "Phase 3": 0.58,
        "Phase 4": 0.95
    }
    
    if not isinstance(trials_data, dict) or "phase_distribution" not in trials_data:
        return {
            "error": "Invalid input format",
            "note": "Expected dictionary with 'phase_distribution' key"
        }
    
    phase_dist = trials_data.get("phase_distribution", {})
    total_trials = sum(phase_dist.values())
    
    if total_trials == 0:
        return {
            "error": "No trials found in the data",
            "note": "Phase distribution is empty"
        }
    
    # Calculate weighted pipeline maturity score
    phase_weights = {"Phase 1": 0.25, "Phase 2": 0.50, "Phase 3": 0.75, "Phase 4": 1.0}
    maturity_score = 0
    
    for phase, count in phase_dist.items():
        if phase in phase_weights:
            maturity_score += (count / total_trials) * phase_weights[phase]
    
    # Detailed maturity assessment
    if maturity_score < 0.35:
        maturity_level = "Early Stage (High Risk)"
        risk_profile = "High attrition risk; significant capital required for progression"
        strategic_recommendation = "Focus on proof-of-concept validation; consider partner co-development"
    elif maturity_score < 0.60:
        maturity_level = "Mid Stage (Moderate Risk)"
        risk_profile = "Phase 2 efficacy validation critical; regulatory pathway clarity needed"
        strategic_recommendation = "Accelerate Phase 2 enrollment; engage regulators for endpoint alignment"
    else:
        maturity_level = "Late Stage (Lower Risk)"
        risk_profile = "Near-term approval potential; focus on market access preparation"
        strategic_recommendation = "Prepare commercialization strategy; initiate payer engagement"
    
    # Calculate expected success probability (compound probability across phases)
    expected_success = 1.0
    for phase, count in phase_dist.items():
        if phase in success_rates and count > 0:
            expected_success *= success_rates[phase]
    
    # Generate insights
    phase_insights = []
    for phase, count in sorted(phase_dist.items()):
        pct = round((count / total_trials) * 100, 1)
        if count > 0:
            insight = f"{phase}: {count} trial(s) ({pct}%) - "
            if "Phase 3" in phase and count >= 2:
                insight += "Strong late-stage commitment, market entry likely"
            elif "Phase 2" in phase and count >= 3:
                insight += "Multiple shots on goal, diversified risk strategy"
            elif "Phase 1" in phase:
                insight += "Early exploration, foundational safety data building"
            else:
                insight += "Post-market surveillance or lifecycle management"
            phase_insights.append(insight)
    
    # Competitive benchmark (industry norms)
    competitive_context = ""
    if total_trials >= 10:
        competitive_context = "Above-average pipeline depth; strong sponsor commitment"
    elif total_trials >= 5:
        competitive_context = "Moderate pipeline activity; selective indication targeting"
    else:
        competitive_context = "Limited pipeline; high-conviction bet on specific indication"
    
    return {
        "total_trials": total_trials,
        "phase_distribution": phase_dist,
        "phase_percentages": {
            phase: round((count / total_trials) * 100, 1)
            for phase, count in phase_dist.items()
        },
        "maturity_score": round(maturity_score, 2),
        "maturity_level": maturity_level,
        "risk_profile": risk_profile,
        "expected_approval_probability": round(expected_success * 100, 1),
        "strategic_recommendation": strategic_recommendation,
        "phase_insights": phase_insights,
        "competitive_context": competitive_context,
        "success_probability_by_phase": success_rates,
        "interpretation": f"Pipeline shows {maturity_level.lower()} with {total_trials} total trials. " +
                         f"Maturity score: {round(maturity_score * 100, 0)}%. {competitive_context}.",
        "key_risks": _identify_key_risks(phase_dist, maturity_score),
        "data_source": "Analysis based on ClinicalTrials.gov pipeline data and industry success rate benchmarks"
    }

def _identify_key_risks(phase_dist: dict, maturity: float) -> list:
    """Identify key development risks based on phase distribution"""
    risks = []
    
    phase_3_count = phase_dist.get("Phase 3", 0) + phase_dist.get("Phase III", 0)
    phase_2_count = phase_dist.get("Phase 2", 0) + phase_dist.get("Phase II", 0)
    
    if phase_3_count == 0 and maturity > 0.4:
        risks.append("No Phase 3 trials despite mid-stage maturity - pivotal data gap")
    
    if phase_2_count == 0:
        risks.append("No Phase 2 trials - efficacy validation missing")
    
    if sum(phase_dist.values()) == 1:
        risks.append("Single trial dependency - high binary outcome risk")
    
    if maturity < 0.3:
        risks.append("Very early pipeline - substantial time and capital to market")
    
    if not risks:
        risks.append("Pipeline appears well-balanced with manageable development risks")
    
    return risks
