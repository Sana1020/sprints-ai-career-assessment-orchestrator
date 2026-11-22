
"""Offline integration tests for the LangGraph orchestrator."""

import pytest
from types import SimpleNamespace

from src.agents.orchestrator import SprintsOrchestrator
from src.tools.db_queries import build_database


class FakeLLM:
    """Return a fixed routing decision without calling an external API."""

    def invoke(self, prompt):
        return SimpleNamespace(content="profile")


class FakeProfileAgent:
    """Simulate a successful ReAct profile response without an API call."""

    def answer(self, question):
        return {
            "status": "ok",
            "answer": "Learner profile checked successfully.",
            "messages": [],
        }


@pytest.fixture(scope="module")
def orchestrator():
    """Create an orchestrator with fake LLM agents for offline tests."""

    build_database()

    instance = SprintsOrchestrator()
    instance.llm = FakeLLM()
    instance.profile_agent = FakeProfileAgent()

    return instance


def test_router_selects_profile(orchestrator):
    result = orchestrator.router({
        "query": "I want placement at Fawry"
    })

    assert result["intent"] == "profile"


def test_route_returns_correct_node(orchestrator):
    assert orchestrator.route({"intent": "profile"}) == "profile"
    assert orchestrator.route({"intent": "advisor"}) == "advisor"
    assert orchestrator.route({"intent": "assessor"}) == "assessor"


def test_hitl_pauses_and_approves_placement(orchestrator):
    thread_id = "pytest-hitl-approve"

    result = orchestrator.invoke(
        query="I want placement at Fawry",
        student_id="SPR-1001",
        thread_id=thread_id
    )

    assert result.get("__interrupt__")

    resumed = orchestrator.approve_placement(
        decision="approve",
        thread_id=thread_id
    )

    assert resumed["human_decision"] == "approved"
    assert resumed["placement"]["status"] == "approved"


def test_hitl_pauses_and_rejects_placement(orchestrator):
    thread_id = "pytest-hitl-reject"

    result = orchestrator.invoke(
        query="I want placement at Fawry",
        student_id="SPR-1001",
        thread_id=thread_id
    )

    assert result.get("__interrupt__")

    resumed = orchestrator.approve_placement(
        decision="reject",
        thread_id=thread_id
    )

    assert resumed["human_decision"] == "rejected"
    assert resumed["placement"]["status"] == "rejected"


def test_missing_learner_does_not_trigger_hitl(orchestrator):
    result = orchestrator.invoke(
        query="I want placement at Fawry",
        student_id="SPR-9999",
        thread_id="pytest-hitl-missing"
    )

    assert not result.get("__interrupt__")
    assert "Unable to verify" in result["answer"]
