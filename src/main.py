
"""Command-line entry point for the Sprints AI Career & Assessment Orchestrator."""

import argparse
import json

from src.agents.orchestrator import SprintsOrchestrator


def main(orchestrator=None, argv=None):
    """Run the CLI with an injectable orchestrator for offline testing."""

    parser = argparse.ArgumentParser(
        description="Sprints AI Career & Assessment Orchestrator"
    )
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--code", default="")

    args = parser.parse_args(argv)

    app = orchestrator if orchestrator is not None else SprintsOrchestrator()

    result = app.invoke(
        args.query,
        args.student_id,
        args.thread_id,
        args.code,
    )

    print(json.dumps(result, default=str, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    main()
