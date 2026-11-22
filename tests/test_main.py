
import json

from src.main import main


class FakeOrchestrator:
    def __init__(self):
        self.received = None

    def invoke(self, query, student_id, thread_id, code):
        self.received = {
            "query": query,
            "student_id": student_id,
            "thread_id": thread_id,
            "code": code,
        }
        return {"status": "ok", "answer": "CLI test successful"}


def test_cli_uses_injected_orchestrator(capsys):
    fake = FakeOrchestrator()

    result = main(
        orchestrator=fake,
        argv=[
            "--student-id", "SPR-1001",
            "--thread-id", "cli-test-001",
            "--query", "Show learner profile",
        ],
    )

    assert result["status"] == "ok"
    assert fake.received == {
        "query": "Show learner profile",
        "student_id": "SPR-1001",
        "thread_id": "cli-test-001",
        "code": "",
    }

    output = json.loads(capsys.readouterr().out)
    assert output["answer"] == "CLI test successful"
