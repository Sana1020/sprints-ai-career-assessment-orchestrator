
"""Offline tests for the curriculum advisor."""

from types import SimpleNamespace

from src.agents.advisor_agent import AdvisorAgent


class FakeLLM:
    """Simulate the advisor LLM without an API call."""

    def __init__(self):
        self.responses = [
            "YES",
            "The evaluator-optimizer pattern uses a producer and a judge. "
            "The loop is limited to three iterations. "
            "Source: 07_evaluator_optimizer.md"
        ]

    def invoke(self, prompt):
        return SimpleNamespace(content=self.responses.pop(0))


class FakeRAG:
    """Return deterministic curriculum evidence."""

    def retrieve(self, query):
        doc = SimpleNamespace(
            metadata={"source_file": "07_evaluator_optimizer.md"},
            page_content=(
                "A producer creates an output and a judge reviews it. "
                "The loop must have a maximum of three iterations."
            )
        )
        return [doc], 25.0


def test_advisor_answers_using_retrieved_context():
    advisor = AdvisorAgent(llm=FakeLLM(), rag=FakeRAG())

    result = advisor.answer(
        "Explain the evaluator optimizer pattern."
    )

    assert "three iterations" in result["answer"]
    assert "07_evaluator_optimizer.md" in result["context"]
    assert result["retrieval_ms"] == 25.0
def test_advisor_retries_when_context_is_insufficient():
    llm = FakeLLM()
    llm.responses = [
        "NO",
        "evaluator optimizer maximum iterations",
        "The loop is limited to three iterations. "
        "Source: 07_evaluator_optimizer.md"
    ]

    rag = FakeRAG()

    advisor = AdvisorAgent(llm=llm, rag=rag)
    result = advisor.answer("How many iterations are allowed?")

    assert "three iterations" in result["answer"]
    assert "07_evaluator_optimizer.md" in result["context"]
    assert len(llm.responses) == 0