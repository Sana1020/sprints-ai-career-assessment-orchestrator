
"""Offline tests for the ProfileAgent."""

from types import SimpleNamespace

from src.agents.profile_agent import ProfileAgent


class FakeAgent:
    """Simulate a tool-calling agent without an external API."""

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.last_input = None

    def invoke(self, input_data):
        self.last_input = input_data

        if self.error:
            raise self.error

        return self.result


def test_profile_agent_handles_empty_messages():
    fake = FakeAgent(result={"messages": []})
    profile = ProfileAgent(agent=fake)

    result = profile.answer("Get learner profile")

    assert result["status"] == "Unable to verify"
    assert "Unable to verify" in result["answer"]
    assert result["messages"] == []


def test_profile_agent_returns_final_answer():
    fake = FakeAgent(
        result={
            "messages": [
                SimpleNamespace(content="Learner score is 95.")
            ]
        }
    )
    profile = ProfileAgent(agent=fake)

    result = profile.answer("Get learner SPR-1001 profile")

    assert result["status"] == "ok"
    assert result["answer"] == "Learner score is 95."
    assert fake.last_input["messages"][0][1] == (
        "Get learner SPR-1001 profile"
    )


def test_profile_agent_handles_exceptions():
    fake = FakeAgent(error=RuntimeError("Database unavailable"))
    profile = ProfileAgent(agent=fake)

    result = profile.answer("Get learner SPR-1001 profile")

    assert result["status"] == "Unable to verify"
    assert "RuntimeError" in result["answer"]
