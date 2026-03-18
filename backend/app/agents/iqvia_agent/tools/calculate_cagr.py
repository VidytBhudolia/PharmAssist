from crewai.tools import tool

@tool("calculate_cagr")
def calculate_cagr(start_value: float, end_value: float, years: int) -> dict:
    """
    Calculates Compound Annual Growth Rate (CAGR) for pharmaceutical market analysis.
    
    Args:
        start_value: Market value at the beginning (in millions USD)
        end_value: Market value at the end (in millions USD)
        years: Number of years in the period
    
    Returns:
        Dictionary containing CAGR percentage and growth analysis
    """
    if years <= 0:
        return {"error": "Years must be greater than 0"}
    
    if start_value <= 0:
        return {"error": "Start value must be greater than 0"}
    
    cagr = (((end_value / start_value) ** (1 / years)) - 1) * 100
    
    total_growth = ((end_value - start_value) / start_value) * 100
    
    return {
        "start_value_usd_millions": start_value,
        "end_value_usd_millions": end_value,
        "period_years": years,
        "cagr_percent": round(cagr, 2),
        "total_growth_percent": round(total_growth, 2),
        "interpretation": f"The market grew at a {round(cagr, 2)}% compound annual growth rate over {years} years."
    }
