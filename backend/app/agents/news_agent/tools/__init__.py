"""News Agent tools — assertion extraction, comparison, and notification persistence."""

from .monitor_tool import (  # noqa: F401
    extract_assertions,
    compare_assertions,
    create_or_update_notification,
)
