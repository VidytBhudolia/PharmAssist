"""
News Monitor Worker — background / manual recheck logic.

For POC the scheduled cron is **disabled by default**. The worker
exposes a ``run_recheck_for_prompt`` function used by the
``POST /news/recheck`` endpoint and a ``run_all_enabled`` sweep used
by a future cron scheduler.

Config toggles live in ``app.core.config``:
    NEWS_MONITOR_CRON_ENABLED  (default False)
    NEWS_MONITOR_INTERVAL_SEC  (default 86400 — 24 h)
    NEWS_MONITOR_RATE_LIMIT_SEC (default 2)
"""

from __future__ import annotations

import time
import datetime
from typing import Any, Dict, List, Optional

from app.core.db import DatabaseManager, init_db
from app.agents.news_agent.news_agent import run_news_agent


# ── Config defaults (override via env / config.py) ────────────────────────

NEWS_MONITOR_CRON_ENABLED: bool = False
NEWS_MONITOR_INTERVAL_SEC: int = 86400  # 24 hours
NEWS_MONITOR_RATE_LIMIT_SEC: float = 2.0  # delay between web calls


def run_recheck_for_prompt(
    db: DatabaseManager,
    session_id: str,
    prompt_id: str,
) -> Dict[str, Any]:
    """Run comparator for a single monitored promptId.

    Called by ``POST /news/recheck`` and by the sweep function.
    """
    session = db.get_session(session_id)
    if not session:
        return {"status": "error", "message": "Session not found"}

    old_agent_data = None
    for entry in session.get("agentsData", []):
        if entry.get("promptId") == prompt_id:
            old_agent_data = entry.get("agents", {})
            break

    if old_agent_data is None:
        return {"status": "error", "message": "promptId not found in session"}

    # Fetch latest uploaded doc (if any)
    new_doc_text = None
    try:
        from app.agents.internal_knowledge_agent.internal_knowledge_agent import (
            get_document_for_session,
        )
        doc_info = get_document_for_session(session_id)
        if doc_info and doc_info.get("parsed_text"):
            new_doc_text = doc_info["parsed_text"]
    except Exception:
        pass

    # Rate-limit guard
    time.sleep(NEWS_MONITOR_RATE_LIMIT_SEC)

    result = run_news_agent(
        session_id=session_id,
        prompt_id=prompt_id,
        old_agent_data=old_agent_data,
        new_document_text=new_doc_text,
        db=db,
    )

    return result


def run_all_enabled(db: Optional[DatabaseManager] = None) -> List[str]:
    """Sweep all notifications where ``enabled=True``.

    Returns list of promptIds that changed status.

    For POC this is invoked **manually only** (NEWS_MONITOR_CRON_ENABLED
    is False by default).
    """
    if db is None:
        db = init_db()

    changed_prompt_ids: List[str] = []

    cursor = db.db["notifications"].find({"enabled": True})

    for notif in cursor:
        session_id = notif.get("sessionId")
        prompt_id = notif.get("promptId")
        if not session_id or not prompt_id:
            continue

        result = run_recheck_for_prompt(db, session_id, prompt_id)
        compare = result.get("data", {}).get("compareResult", {})
        if compare.get("status") == "changed":
            changed_prompt_ids.append(prompt_id)

    return changed_prompt_ids


# ── Optional: cron-like entry point ───────────────────────────────────────
# To enable, set NEWS_MONITOR_CRON_ENABLED=True and run this module
# as a standalone process:
#     python -m app.workers.news_monitor_worker
# It will loop every NEWS_MONITOR_INTERVAL_SEC and call run_all_enabled.

def _cron_loop():  # pragma: no cover
    """Blocking event loop for scheduled monitoring (disabled by default)."""
    if not NEWS_MONITOR_CRON_ENABLED:
        print("[NewsWorker] Cron is disabled. Set NEWS_MONITOR_CRON_ENABLED=True to enable.")
        return

    db = init_db()
    print(f"[NewsWorker] Starting cron loop (interval={NEWS_MONITOR_INTERVAL_SEC}s)")

    while True:
        try:
            changed = run_all_enabled(db)
            print(f"[NewsWorker] Sweep complete — {len(changed)} changed: {changed}")
        except Exception as exc:
            print(f"[NewsWorker] Error during sweep: {exc}")

        time.sleep(NEWS_MONITOR_INTERVAL_SEC)


if __name__ == "__main__":
    _cron_loop()
