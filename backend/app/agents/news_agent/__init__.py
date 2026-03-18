"""News Agent — Research monitor that detects material changes in previously
completed research (patent events, regulatory/trade changes, or uploaded
internal docs) and notifies the user if re-evaluation is recommended."""

from .news_agent import run_news_agent  # noqa: F401

__all__ = ["run_news_agent"]
