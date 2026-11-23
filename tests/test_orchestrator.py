
"""Offline integration tests for the LangGraph orchestrator."""

import pytest
from types import SimpleNamespace

from src.agents.orchestrator import SprintsOrchestrator
from src.tools.db_queries import build_database


class FakeLLM:
    """Route requests to the profile agent."""

    def invoke(self, prompt):
        return SimpleNamespace(content="profile")


class FakeAdvisorRouterLLM:
    """Route requests to the advisor agent."""

    def invoke(self, prompt):
        return SimpleNamespace(content="advisor")


class FakeProfileAgent:
    """Simulate a successful profile response."""

    def answer(self, question):
        return {
            "status": "ok",
            "answer": "Learner profile checked successfully.",
            "messages": [],
        }


class FakeAdvisor:
    """Simulate advisor retrieval and reflection."""

    def __init__(self, sufficient_after=1):
        self.retrieve_calls = 0
        self.reflect_calls = 0
        self.sufficient_after = sufficient_after

    def retrieve(self, question):
        self.retrieve_calls += 1
        return {
            "advisor_docs": [],
            "advisor_context": f"Retrieved context for: {question}",
            "retrieval_ms": 5.0,
        }

    def reflect(self, question, context):
        self.reflect_calls += 1
        return self.reflect_calls >= self.sufficient_after

    def rewrite_query(self, question):
        return f"Rewritten: {question}"

    def generate_answer(self, question, context):
        return "Answer generated from retrieved context."


@pytest.fixture(scope="module")
def orchestrator():
    """Create an orchestrator with fake agents for offline tests."""

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
        thread_id=thread_id,
    )

    assert result.get("__interrupt__")

    resumed = orchestrator.approve_placement(
        decision="approve",
        thread_id=thread_id,
    )

    assert resumed["human_decision"] == "approved"
    assert resumed["placement"]["status"] == "approved"


def test_hitl_pauses_and_rejects_placement(orchestrator):
    thread_id = "pytest-hitl-reject"

    result = orchestrator.invoke(
        query="I want placement at Fawry",
        student_id="SPR-1001",
        thread_id=thread_id,
    )

    assert result.get("__interrupt__")

    resumed = orchestrator.approve_placement(
        decision="reject",
        thread_id=thread_id,
    )

    assert resumed["human_decision"] == "rejected"
    assert resumed["placement"]["status"] == "rejected"


def test_missing_learner_does_not_trigger_hitl(orchestrator):
    result = orchestrator.invoke(
        query="I want placement at Fawry",
        student_id="SPR-9999",
        thread_id="pytest-hitl-missing",
    )

    assert not result.get("__interrupt__")
    assert "Unable to verify" in result["answer"]


def test_advisor_self_reflection_graph_workflow():
    """Verify advisor retrieval, reflection, and retry limit."""

    # Case 1: Context is sufficient on the first attempt.
    advisor = FakeAdvisor(sufficient_after=1)

    instance = SprintsOrchestrator(
        llm=FakeAdvisorRouterLLM(),
        advisor=advisor,
    )

    result = instance.app.invoke(
        {
            "query": "Explain RAG",
            "student_id": "SPR-1001",
            "thread_id": "advisor-first-pass",
            "messages": [],
            "advisor_retry_count": 0,
            "retrieval_ms": 0.0,
        },
        config={
            "configurable": {
                "thread_id": "advisor-first-pass"
            }
        },
    )

    assert result["answer"] == "Answer generated from retrieved context."
    assert advisor.retrieve_calls == 1
    assert advisor.reflect_calls == 1
    assert result["advisor_retry_count"] == 0

    # Case 2: One rewrite and a second retrieval are required.
    advisor = FakeAdvisor(sufficient_after=2)

    instance = SprintsOrchestrator(
        llm=FakeAdvisorRouterLLM(),
        advisor=advisor,
    )

    result = instance.app.invoke(
        {
            "query": "Explain RAG",
            "student_id": "SPR-1001",
            "thread_id": "advisor-retry",
            "messages": [],
            "advisor_retry_count": 0,
            "retrieval_ms": 0.0,
        },
        config={
            "configurable": {
                "thread_id": "advisor-retry"
            }
        },
    )

    assert result["answer"] == "Answer generated from retrieved context."
    assert advisor.retrieve_calls == 2
    assert advisor.reflect_calls == 2
    assert result["advisor_retry_count"] == 1

    # Case 3: The maximum of two reformulations is respected.
    advisor = FakeAdvisor(sufficient_after=999)

    instance = SprintsOrchestrator(
        llm=FakeAdvisorRouterLLM(),
        advisor=advisor,
    )

    result = instance.app.invoke(
        {
            "query": "Explain RAG",
            "student_id": "SPR-1001",
            "thread_id": "advisor-max-retries",
            "messages": [],
            "advisor_retry_count": 0,
            "retrieval_ms": 0.0,
        },
        config={
            "configurable": {
                "thread_id": "advisor-max-retries"
            }
        },
    )

    assert result["answer"] == "Answer generated from retrieved context."
    assert advisor.retrieve_calls == 3
    assert advisor.reflect_calls == 3
    assert result["advisor_retry_count"] == 2

def test_message_logging_trace(orchestrator, caplog):
    """Verify Human, AI, and Tool logging without external API calls."""

    import logging

    caplog.set_level(logging.INFO)

    orchestrator.invoke(
        query="Show my learner profile",
        student_id="SPR-1001",
        thread_id="pytest-logging-trace",
    )

    logs = "\n".join(
        record.getMessage()
        for record in caplog.records
    )

    assert "HumanMessage" in logs
    assert "AIMessage" in logs
    assert "ToolMessage" in logs
    assert "get_learner_profile_tool" in logs
