
"""Bounded Python submission runner for assessment demonstrations.

IMPORTANT:
This is a restricted demo runner, NOT a secure sandbox for untrusted code.
Production execution requires disposable OS-level containers with network
disabled, resource limits, a non-root user and filesystem isolation.
"""

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from langchain_core.tools import tool

BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "requests", "urllib",
    "shutil", "pathlib", "ctypes", "multiprocessing",
}

BLOCKED_CALLS = {
    "eval", "exec", "compile", "__import__", "input", "open",
    "globals", "locals", "getattr", "setattr", "delattr",
}

MAX_OUTPUT = 4000


def static_check(code: str) -> list[str]:
    """Return static validation issues without executing the submission."""
    issues = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"SyntaxError: {exc}"]

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                names = [item.name.split(".")[0] for item in node.names]
            else:
                names = [(node.module or "").split(".")[0]]

            for name in names:
                if name in BLOCKED_IMPORTS:
                    issues.append(f"Blocked import: {name}")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_CALLS:
                issues.append(f"Blocked call: {node.func.id}")

        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            issues.append("Blocked access to dunder attributes")

    return list(dict.fromkeys(issues))



def _execute_python(code: str, timeout_seconds: int = 3,
                    blocked_status: str = "blocked") -> dict:
    """Execute code after static checks and capture bounded output."""
    issues = static_check(code)

    if issues:
        return {
            "status": blocked_status,
            "stdout": "",
            "stderr": "; ".join(issues)[:2000],
        }

    try:
        with tempfile.TemporaryDirectory(prefix="sprints_submission_") as tmp:
            script = Path(tmp) / "submission.py"
            script.write_text(code, encoding="utf-8")

            env = {
                "PATH": os.environ.get("PATH", ""),
                "PYTHONIOENCODING": "utf-8",
            }

            proc = subprocess.run(
                [sys.executable, "-I", str(script)],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            return {
                "status": "ok" if proc.returncode == 0 else "error",
                "stdout": proc.stdout[:MAX_OUTPUT],
                "stderr": proc.stderr[:2000],
                "return_code": proc.returncode,
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "stdout": "",
            "stderr": "Execution time limit exceeded",
        }

    except Exception as exc:
        return {
            "status": "Unable to verify",
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def execute_python(code: str, timeout_seconds: int = 3) -> dict:
    """Execute code and return Unable to verify for blocked submissions."""
    return _execute_python(code, timeout_seconds, "Unable to verify")


def run_python(code: str, timeout_s: int = 3) -> dict:
    """Run a learner submission with an explicit blocked status."""
    result = execute_python(code, timeout_seconds=timeout_s)

    if (
        result["status"] == "Unable to verify"
        and result.get("stderr", "").startswith("Blocked")
    ):
        result["status"] = "blocked"

    return result


@tool
def run_student_python(code: str) -> dict:
    """Run a Sprints Python exercise with captured output and errors."""
    return execute_python(code)
