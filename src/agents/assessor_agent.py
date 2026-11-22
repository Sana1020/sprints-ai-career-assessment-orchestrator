
"""Structured Python assessor with a bounded evaluator-optimizer loop."""

from typing import List

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from src.tools.code_repl import execute_python
from src.config import PASS_MARK


class Assessment(BaseModel):
    """Structured assessment returned to the learner."""

    score: int = Field(ge=0, le=100)
    feedback_points: List[str]
    pass_status: bool
    execution_status: str


class AssessorAgent:
    """Execute student code, assess it, and refine feedback up to 3 times."""

    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        self.structured = self.llm.with_structured_output(Assessment)

    def assess(
        self,
        prompt,
        code,
        expected_behavior="Correctly solve the assigned exercise"
    ):
        """Execute, evaluate, and refine an assessment."""

        # 1. Execute student code
        try:
            execution = execute_python(code)
        except Exception as exc:
            return {
                "status": "Unable to verify",
                "reason": f"Code execution failed: {type(exc).__name__}"
            }

        if execution["status"] not in ("ok", "runtime_error"):
            return {
                "status": "Unable to verify",
                "reason": execution.get("stderr") or "Execution failed"
            }

        # 2. Define the grading rubric
        rubric = (
            "Correctness: 60 points. "
            "Required concepts: 20 points. "
            "Edge cases: 10 points. "
            "Code clarity: 10 points. "
            "Do not assume code is correct just because it executes successfully."
        )

        optimizer_instruction = (
            "This is the initial assessment. Evaluate the code carefully."
        )

        # 3. Evaluator-Optimizer loop (maximum 3 iterations)
        try:
            for iteration in range(3):

                candidate = self.structured.invoke([
                    (
                        "system",
                        "You are a careful Sprints Python assessor. "
                        "Evaluate the learner's solution using the rubric "
                        "and return the required structured schema."
                    ),
                    (
                        "human",
                        f"Task: {prompt}\n"
                        f"Expected behavior: {expected_behavior}\n"
                        f"Code:\n{code}\n"
                        f"Execution status: {execution['status']}\n"
                        f"stdout:\n{execution.get('stdout', '')}\n"
                        f"stderr:\n{execution.get('stderr', '')}\n"
                        f"Rubric: {rubric}\n"
                        f"Iteration: {iteration + 1}/3\n"
                        f"Previous evaluator feedback: {optimizer_instruction}"
                    )
                ])

                # 4. Independent LLM judge
                judge_response = self.llm.invoke(
                    "Review this assessment against the task and rubric. "
                    "Reply with exactly APPROVE if justified. "
                    "Otherwise, provide one concise correction instruction.\n\n"
                    + candidate.model_dump_json()
                )

                judge = judge_response.content.strip()

                if judge.upper().startswith("APPROVE"):
                    break

                optimizer_instruction = judge

        except Exception as exc:
            return {
                "status": "Unable to verify",
                "reason": (
                    "Assessment generation failed: "
                    f"{type(exc).__name__}"
                )
            }

        # 5. Build final result
        result = candidate.model_dump()

        result["execution_status"] = execution["status"]

        result["pass_status"] = (
            result["score"] >= PASS_MARK
            and execution["status"] == "ok"
        )

        result["refinement_iterations"] = iteration + 1

        return {
            "status": "ok",
            "assessment": result,
            "execution": execution
        }
