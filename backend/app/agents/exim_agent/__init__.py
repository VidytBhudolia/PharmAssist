# Import tools directly - agent is lazily loaded to avoid LLM initialization issues
from .tools.fetch_exim_data import fetch_exim_data

__all__ = [
    "fetch_exim_data",
    "run_exim_agent",
    "get_exim_agent",
]


def run_exim_agent(user_prompt: str, **kwargs) -> dict:
    """Run the EXIM agent with LLM parameter extraction."""
    from .exim_agent import run_exim_agent as _run_exim_agent
    return _run_exim_agent(user_prompt, **kwargs)


# Agent is available but not auto-imported to avoid LLM initialization
def get_exim_agent():
    """Lazily load the EXIM agent. Only call this when you have LiteLLM configured."""
    from .exim_agent import exim_agent

    return exim_agent
