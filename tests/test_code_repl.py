
from src.tools.code_repl import execute_python

def test_simple_code_runs():
    result = execute_python("print(2 + 2)")
    assert result["status"] == "ok"
    assert result["stdout"].strip() == "4"

def test_blocked_import():
    result = execute_python("import os\nprint(os.getcwd())")
    assert result["status"] == "Unable to verify"
