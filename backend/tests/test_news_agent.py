"""
Unit & integration tests for the News Agent.

Run:
    pytest backend/tests/test_news_agent.py -v
"""

from __future__ import annotations

import copy
import uuid
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from app.agents.news_agent.tools.monitor_tool import (
    extract_assertions,
    compare_assertions,
    create_or_update_notification,
)
from app.agents.news_agent.news_agent import run_news_agent


# ═══════════════════════════════════════════════════════════════════════════
#  Fixtures: Representative Agent Outputs
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def patent_agent_data() -> Dict[str, Any]:
    """Typical PATENT_AGENT data with two patents."""
    return {
        "PATENT_AGENT": {
            "data": {
                "patents": [
                    {
                        "patentNumber": "US9855251",
                        "expiry": "2032-06-15",
                        "claimType": "composition",
                        "title": "Semaglutide Composition Patent",
                        "blocking": True,
                    },
                    {
                        "patentNumber": "US10238710",
                        "expiry": "2035-01-20",
                        "claimType": "method_of_use",
                        "title": "Method of Treating Obesity",
                        "blocking": False,
                    },
                ],
                "fto": {"risk_level": "medium"},
            }
        }
    }


@pytest.fixture
def exim_agent_data() -> Dict[str, Any]:
    """Typical EXIM_AGENT data."""
    return {
        "EXIM_AGENT": {
            "data": {
                "total_trade_value": 125_000_000,
                "llm_insights": {
                    "import_dependency": {
                        "dependency_ratio": 0.42,
                        "yoy_change": 0.03,
                    },
                    "supply_chain_risk": {
                        "risk_level": "moderate",
                    },
                },
            }
        }
    }


@pytest.fixture
def web_intel_data() -> Dict[str, Any]:
    """Typical WEB_INTELLIGENCE_AGENT data with a news article."""
    return {
        "WEB_INTELLIGENCE_AGENT": {
            "data": {
                "news": [
                    {"title": "FDA Issues New Warning on GLP-1 Agonists"},
                    {"title": "Good Manufacturing Practices Updated"},
                ],
            }
        }
    }


@pytest.fixture
def internal_knowledge_data() -> Dict[str, Any]:
    """Typical INTERNAL_KNOWLEDGE_AGENT data."""
    return {
        "INTERNAL_KNOWLEDGE_AGENT": {
            "data": {
                "strategic_synthesis": {
                    "description": "Semaglutide has a strong IP position with blocking patents through 2032.",
                }
            }
        }
    }


@pytest.fixture
def combined_old_data(
    patent_agent_data, exim_agent_data, web_intel_data, internal_knowledge_data
) -> Dict[str, Any]:
    """Combined multi-agent output used as the 'old' baseline."""
    merged = {}
    merged.update(patent_agent_data)
    merged.update(exim_agent_data)
    merged.update(web_intel_data)
    merged.update(internal_knowledge_data)
    return merged


@pytest.fixture
def raw_document_text() -> str:
    """Representative uploaded document text."""
    return (
        "Internal Pharma Report — Q1 2025\n"
        "Patent US9855251 has been invalidated as of March 2025.\n"
        "Import restrictions may apply due to new embargo on raw intermediates.\n"
        "Market size estimate revised to $1.2B.\n"
        "Blocking patent no longer enforceable per recent court ruling.\n"
        "Recommendation: proceed with generic formulation.\n"
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Unit Tests — extract_assertions
# ═══════════════════════════════════════════════════════════════════════════

class TestExtractAssertions:
    """Verify extract_assertions produces correct normalized structures."""

    def test_empty_input(self):
        result = extract_assertions(None)
        assert result["patents"] == []
        assert result["trade"] == {}
        assert result["regulatory"] == []

    def test_patent_extraction(self, patent_agent_data):
        result = extract_assertions(patent_agent_data)
        assert len(result["patents"]) == 2
        assert result["patents"][0]["patentNumber"] == "US9855251"
        assert result["patents"][0]["blocking"] is True
        assert result["patents"][1]["claimType"] == "method_of_use"

    def test_trade_extraction(self, exim_agent_data):
        result = extract_assertions(exim_agent_data)
        assert result["trade"]["import_dependency"] == pytest.approx(0.42)
        assert result["trade"]["yoy_change"] == pytest.approx(0.03)

    def test_regulatory_extraction(self, web_intel_data):
        result = extract_assertions(web_intel_data)
        keywords = [r["keyword"] for r in result["regulatory"]]
        assert "warning" in keywords

    def test_internal_doc_extraction(self, internal_knowledge_data):
        result = extract_assertions(internal_knowledge_data)
        assert len(result["internal_doc_assertions"]) >= 1
        assert "blocking" in result["internal_doc_assertions"][0]["statement"].lower()

    def test_combined_extraction(self, combined_old_data):
        result = extract_assertions(combined_old_data)
        assert len(result["patents"]) == 2
        assert result["trade"]["import_dependency"] == pytest.approx(0.42)
        assert len(result["regulatory"]) >= 1
        assert len(result["internal_doc_assertions"]) >= 1

    def test_raw_text_extraction(self, raw_document_text):
        result = extract_assertions({"_raw_text": raw_document_text})
        # Should find patent references
        patent_nums = [p["patentNumber"] for p in result["patents"]]
        assert any("9855251" in pn for pn in patent_nums)
        # Should find regulatory keywords
        keywords = [r["keyword"] for r in result["regulatory"]]
        assert "embargo" in keywords
        # Should have doc assertions
        assert len(result["internal_doc_assertions"]) > 0


# ═══════════════════════════════════════════════════════════════════════════
#  Unit Tests — compare_assertions
# ═══════════════════════════════════════════════════════════════════════════

class TestCompareAssertions:
    """Verify compare_assertions severity rules."""

    def test_no_change(self, combined_old_data):
        """Identical data should yield 'secure'."""
        old = extract_assertions(combined_old_data)
        new = extract_assertions(combined_old_data)
        result = compare_assertions(old, new)
        assert result["status"] == "secure"
        assert result["changedFields"] == []

    def test_new_blocking_patent_high_severity(self, combined_old_data):
        """Adding a new blocking patent → severity HIGH."""
        old = extract_assertions(combined_old_data)
        modified = copy.deepcopy(combined_old_data)
        modified["PATENT_AGENT"]["data"]["patents"].append({
            "patentNumber": "US11223344",
            "expiry": "2040-01-01",
            "claimType": "composition",
            "title": "New Blocking Patent",
            "blocking": True,
        })
        new = extract_assertions(modified)
        result = compare_assertions(old, new)
        assert result["status"] == "changed"
        assert "patents" in result["changedFields"]
        assert result["severity"] == "high"

    def test_expiry_change_medium_severity(self, combined_old_data):
        """Changing patent expiry → severity MEDIUM."""
        old = extract_assertions(combined_old_data)
        modified = copy.deepcopy(combined_old_data)
        modified["PATENT_AGENT"]["data"]["patents"][0]["expiry"] = "2028-06-15"  # Earlier
        new = extract_assertions(modified)
        result = compare_assertions(old, new)
        assert result["status"] == "changed"
        assert "patents" in result["changedFields"]
        assert result["severity"] in ("medium", "high")

    def test_non_blocking_patent_low_severity(self, combined_old_data):
        """Adding a non-blocking patent → severity LOW."""
        old = extract_assertions(combined_old_data)
        modified = copy.deepcopy(combined_old_data)
        modified["PATENT_AGENT"]["data"]["patents"].append({
            "patentNumber": "US99887766",
            "expiry": "2045-01-01",
            "claimType": "process",
            "title": "Minor Process Patent",
            "blocking": False,
        })
        new = extract_assertions(modified)
        result = compare_assertions(old, new)
        assert result["status"] == "changed"
        assert result["severity"] == "low"

    def test_large_trade_change_high_severity(self, combined_old_data):
        """Import dependency jump >10pp → severity HIGH."""
        old = extract_assertions(combined_old_data)
        modified = copy.deepcopy(combined_old_data)
        # Jump dependency from 0.42 to 0.58 (16pp delta)
        modified["EXIM_AGENT"]["data"]["llm_insights"]["import_dependency"]["dependency_ratio"] = 0.58
        new = extract_assertions(modified)
        result = compare_assertions(old, new)
        assert result["status"] == "changed"
        assert "trade" in result["changedFields"]
        assert result["severity"] == "high"

    def test_small_trade_change_ignored(self, combined_old_data):
        """Very small dep ratio change should NOT trigger a change."""
        old = extract_assertions(combined_old_data)
        modified = copy.deepcopy(combined_old_data)
        # Tiny change: 0.42 → 0.43  (1pp)
        modified["EXIM_AGENT"]["data"]["llm_insights"]["import_dependency"]["dependency_ratio"] = 0.43
        new = extract_assertions(modified)
        result = compare_assertions(old, new)
        # Should stay secure or, if flagged, severity=low
        if result["status"] == "changed":
            assert result["severity"] == "low"

    def test_contradictory_doc_high_severity(self, combined_old_data, raw_document_text):
        """Internal doc contradicting blocking patent → severity HIGH + manual review."""
        old = extract_assertions(combined_old_data)
        new = extract_assertions({"_raw_text": raw_document_text})
        result = compare_assertions(old, new)
        assert result["status"] == "changed"
        # Should detect contradiction or patent change
        assert any(f in result["changedFields"] for f in ["internal_doc", "patents", "regulatory"])
        assert result["severity"] in ("medium", "high")

    def test_both_empty_secure(self):
        """Both empty → secure."""
        result = compare_assertions({}, {})
        assert result["status"] == "secure"

    def test_yoy_sign_flip_medium_severity(self):
        """YoY sign flip > 20% change → severity MEDIUM."""
        old = {
            "patents": [],
            "trade": {"import_dependency": 0.42, "yoy_change": 0.15, "trade_total": 100_000_000},
            "market": {},
            "regulatory": [],
            "internal_doc_assertions": [],
            "other_flags": [],
        }
        new = copy.deepcopy(old)
        new["trade"]["yoy_change"] = -0.10  # sign flip from +15% to -10%, delta 25pp
        result = compare_assertions(old, new)
        assert result["status"] == "changed"
        assert result["severity"] in ("medium", "high")


# ═══════════════════════════════════════════════════════════════════════════
#  Unit Tests — create_or_update_notification
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateOrUpdateNotification:
    """Test notification persistence with mocked DB."""

    def _make_mock_db(self, existing_doc=None):
        db = MagicMock()
        notifications_coll = MagicMock()
        db.db.__getitem__ = MagicMock(return_value=notifications_coll)
        notifications_coll.find_one.return_value = existing_doc
        return db, notifications_coll

    def test_create_new_notification(self):
        db, coll = self._make_mock_db(existing_doc=None)
        compare_result = {
            "status": "changed",
            "changedFields": ["patents"],
            "severity": "high",
            "diffDetails": {"patents": {"oldValue": "2", "newValue": "3"}},
            "requiresManualReview": False,
            "decision_reason": "New blocking patent detected",
        }
        result = create_or_update_notification(db, "sess1", "pid1", compare_result)
        assert result is not None
        assert result["status"] == "changed"
        assert result["severity"] == "high"
        coll.insert_one.assert_called_once()

    def test_update_existing_notification(self):
        existing = {
            "_id": "abc123",
            "notificationId": "nid-old",
            "status": "secure",
            "severity": "low",
        }
        db, coll = self._make_mock_db(existing_doc=existing)
        compare_result = {
            "status": "changed",
            "changedFields": ["trade"],
            "severity": "medium",
            "diffDetails": {"trade": {"oldValue": "0.42", "newValue": "0.58"}},
            "requiresManualReview": False,
            "decision_reason": "Import dependency increased",
        }
        result = create_or_update_notification(db, "sess1", "pid1", compare_result)
        assert result is not None
        coll.update_one.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════
#  Unit Tests — run_news_agent (end-to-end with mocked DB)
# ═══════════════════════════════════════════════════════════════════════════

class TestRunNewsAgent:
    """Test the top-level run_news_agent function."""

    def test_basic_comparison(self, combined_old_data, raw_document_text):
        db = MagicMock()
        notifications_coll = MagicMock()
        db.db.__getitem__ = MagicMock(return_value=notifications_coll)
        notifications_coll.find_one.return_value = None

        result = run_news_agent(
            session_id="test-session",
            prompt_id="test-prompt",
            old_agent_data=combined_old_data,
            new_document_text=raw_document_text,
            db=db,
        )
        assert result["status"] == "success"
        assert "compareResult" in result["data"]
        assert "notification" in result["data"]
        # Notification should have been created
        notifications_coll.insert_one.assert_called_once()

    def test_no_old_data(self):
        """When old data is None, should still succeed."""
        db = MagicMock()
        notifications_coll = MagicMock()
        db.db.__getitem__ = MagicMock(return_value=notifications_coll)
        notifications_coll.find_one.return_value = None

        result = run_news_agent(
            session_id="s1",
            prompt_id="p1",
            old_agent_data=None,
            new_agent_data=None,
            db=db,
        )
        assert result["status"] == "success"

    def test_agent_to_agent_comparison(self, combined_old_data):
        """Compare old agent data to modified new agent data."""
        db = MagicMock()
        notifications_coll = MagicMock()
        db.db.__getitem__ = MagicMock(return_value=notifications_coll)
        notifications_coll.find_one.return_value = None

        modified = copy.deepcopy(combined_old_data)
        modified["PATENT_AGENT"]["data"]["patents"].append({
            "patentNumber": "US55667788",
            "expiry": "2042-01-01",
            "claimType": "composition",
            "title": "New Blocking Patent",
            "blocking": True,
        })

        result = run_news_agent(
            session_id="s1",
            prompt_id="p1",
            old_agent_data=combined_old_data,
            new_agent_data=modified,
            db=db,
        )
        assert result["status"] == "success"
        comp = result["data"]["compareResult"]
        assert comp["status"] == "changed"
        assert comp["severity"] == "high"

    def test_no_db(self, combined_old_data, raw_document_text):
        """When db=None, should still return compare result without crash."""
        result = run_news_agent(
            session_id="s1",
            prompt_id="p1",
            old_agent_data=combined_old_data,
            new_document_text=raw_document_text,
            db=None,
        )
        assert result["status"] == "success"
        assert result["data"]["notification"] is None


# ═══════════════════════════════════════════════════════════════════════════
#  Integration Test — Full Flow (mocked DB)
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegrationFlow:
    """Simulate: create session → enable monitoring → upload doc → recheck."""

    def test_full_monitoring_lifecycle(self, combined_old_data, raw_document_text):
        """
        1. Create notification (enable monitoring)
        2. Run comparator with new doc
        3. Assert notification updated
        """
        # Mock DB
        db = MagicMock()
        notifications_coll = MagicMock()
        db.db.__getitem__ = MagicMock(return_value=notifications_coll)

        # Step 1: First call — no existing notification
        notifications_coll.find_one.return_value = None

        result1 = run_news_agent(
            session_id="integration-session",
            prompt_id="integration-prompt",
            old_agent_data=combined_old_data,
            db=db,
        )
        assert result1["status"] == "success"
        # With no new data, should be secure
        assert result1["data"]["compareResult"]["status"] == "secure"

        # Step 2: Second call — doc uploaded, existing notification exists
        notifications_coll.find_one.return_value = {
            "_id": "mongo-object-id",
            "notificationId": "nid-1",
            "status": "secure",
            "severity": "low",
        }

        result2 = run_news_agent(
            session_id="integration-session",
            prompt_id="integration-prompt",
            old_agent_data=combined_old_data,
            new_document_text=raw_document_text,
            db=db,
        )
        assert result2["status"] == "success"
        comp = result2["data"]["compareResult"]
        # Doc contains contradictions → should be changed
        assert comp["status"] == "changed"
        assert len(comp["changedFields"]) > 0
        # Notification should have been updated
        notifications_coll.update_one.assert_called()
