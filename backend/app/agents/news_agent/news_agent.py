"""
News Agent — Research Monitor

Role: "Research monitor that detects material changes in previously completed
research (patent events, regulatory/trade changes, or uploaded internal docs)
and notifies the user if re-evaluation is recommended."

Design:
- LLM usage is minimal and deterministic where possible.
- The agent is OPTIONAL: only runs when user enables monitoring or when a
  manual recheck is invoked.
- Uses tools/monitor_tool.py for assertion extraction + comparison.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Dict, Optional

from .tools.monitor_tool import (
    extract_assertions,
    compare_assertions,
    create_or_update_notification,
)


def run_news_agent(
    session_id: str,
    prompt_id: str,
    *,
    old_agent_data: Optional[Dict[str, Any]] = None,
    new_agent_data: Optional[Dict[str, Any]] = None,
    new_document_text: Optional[str] = None,
    db=None,
) -> Dict[str, Any]:
    """Run the News Agent comparator for a given promptId.

    Parameters
    ----------
    session_id : str
        The session owning the monitored prompt.
    prompt_id : str
        The original promptId whose data is being monitored.
    old_agent_data : dict | None
        Previously stored agent outputs (unwrapped).
    new_agent_data : dict | None
        Fresh agent outputs or data to compare against.
    new_document_text : str | None
        Parsed text from a newly uploaded document.
    db : DatabaseManager | None
        Database handle for persisting notification.

    Returns
    -------
    dict   { status, notification }
    """
    try:
        # 1. Extract assertions from old data
        old_assertions = extract_assertions(old_agent_data) if old_agent_data else {}

        # 2. Extract assertions from new data (agent outputs or uploaded doc)
        if new_document_text:
            new_assertions = extract_assertions({"_raw_text": new_document_text})
        elif new_agent_data:
            new_assertions = extract_assertions(new_agent_data)
        else:
            new_assertions = {}

        # 3. Compare
        compare_result = compare_assertions(old_assertions, new_assertions)

        # 4. Persist notification
        notification = None
        if db is not None:
            notification = create_or_update_notification(
                db, session_id, prompt_id, compare_result
            )

        return {
            "status": "success",
            "data": {
                "compareResult": compare_result,
                "notification": notification,
            },
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": f"News Agent failed: {exc}",
        }
