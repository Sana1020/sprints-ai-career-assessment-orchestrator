
"""Offline tests for the Python assessor."""

from types import SimpleNamespace

from src.agents.assessor_agent import AssessorAgent, Assessment


class FakeStructuredLLM:
    def __init__(self, scores):
        self.scores = iter(scores)
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return Assessment(
            score=next(self.scores),
            feedback_points=["Reviewed against the rubric"],
            pass_status=True,
            execution_status="ok",
        )


class FakeLLM:
    def __init__(self, scores, judge_responses):
        self.structured_fake = FakeStructuredLLM(scores)
        self.judge_responses = iter(judge_responses)

    def with_structured_output(self, schema):
        assert schema is Assessment
        return self.structured_fake

    def invoke(self, prompt):
        return SimpleNamespace(content=next(self.judge_responses))


class FailingStructuredLLM:
    """Simulate an LLM failure during assessment generation."""

    def invoke(self, prompt):
        raise RuntimeError("LLM service unavailable")


class FailingLLM:
    def with_structured_output(self, schema):
        return FailingStructuredLLM()


def test_assessor_grades_successful_code():
    fake_llm = FakeLLM(
        scores=[90],
        judge_responses=["APPROVE"],
    )

    assessor = AssessorAgent(llm=fake_llm)
    result = assessor.assess(
        prompt="Print the sum of 2 and 2",
        code="print(2 + 2)",
    )

    assert result["status"] == "ok"
    assert result["assessment"]["score"] == 90
    assert result["assessment"]["pass_status"] is True
    assert result["assessment"]["refinement_iterations"] == 1
    assert result["execution"]["stdout"].strip() == "4"


def test_assessor_stops_after_maximum_three_iterations():
    fake_llm = FakeLLM(
        scores=[60, 70, 80],
        judge_responses=[
            "Needs correction",
            "Needs another correction",
            "Needs final correction",
        ],
    )

    assessor = AssessorAgent(llm=fake_llm)
    result = assessor.assess(
        prompt="Print the sum of 2 and 2",
        code="print(2 + 2)",
    )

    assert result["status"] == "ok"
    assert result["assessment"]["refinement_iterations"] == 3
    assert fake_llm.structured_fake.calls == 3
    assert result["assessment"]["score"] == 80


def test_assessor_rejects_blocked_code_without_llm():
    fake_llm = FakeLLM(
        scores=[],
        judge_responses=[],
    )

    assessor = AssessorAgent(llm=fake_llm)
    result = assessor.assess(
        prompt="Print something",
        code="import os\nprint('test')",
    )

    assert result["status"] == "Unable to verify"
    assert fake_llm.structured_fake.calls == 0


def test_assessor_handles_llm_failure():
    assessor = AssessorAgent(llm=FailingLLM())

    result = assessor.assess(
        prompt="Print the sum of 2 and 2",
        code="print(2 + 2)",
    )

    assert result["status"] == "Unable to verify"
    assert "RuntimeError" in result["reason"]
