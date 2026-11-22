"""Offline tests (stdlib only): SQL tool, Python sandbox and 'Unable to verify' fallbacks."""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.config import UNABLE_TO_VERIFY
from src.tools.code_repl import run_python, static_check
from src.tools.db_queries import build_database, get_learner_profile, run_readonly_query


def test_profile_returns_expected_fields():
    build_database(force=True)
    r = get_learner_profile("SPR-1001")
    row = r["rows"][0]
    assert row["target_salary_egp"] == 30000 and "Fawry" in row["preferred_employers"]


def test_sql_fallbacks():
    assert get_learner_profile("SPR-9999")["status"] == UNABLE_TO_VERIFY
    assert get_learner_profile("SPR-1001; DROP TABLE learners")["status"] == UNABLE_TO_VERIFY
    assert run_readonly_query("DELETE FROM learners")["status"] == UNABLE_TO_VERIFY
    assert run_readonly_query("SELECT 1; SELECT 2")["status"] == UNABLE_TO_VERIFY
    assert run_readonly_query("SELECT 1", db_path="/nonexistent/x.sqlite")["status"] == UNABLE_TO_VERIFY


def test_sql_cannot_write_even_via_cte():
    r = run_readonly_query("WITH x AS (SELECT 1) INSERT INTO learners VALUES ('a','b','c',1,1,1,'d','e')")
    assert r["status"] == UNABLE_TO_VERIFY


def test_repl_captures_stdout_and_errors():
    assert run_python("print(2+3)")["stdout"].strip() == "5"
    err = run_python("1/0")
    assert err["status"] == "error" and "ZeroDivisionError" in err["stderr"]


def test_repl_blocks_dangerous_code_and_timeouts():
    assert run_python("import os")["status"] == "blocked"
    assert run_python("open('/etc/passwd').read()")["status"] == "blocked"
    assert run_python("().__class__.__bases__")["status"] == "blocked"
    assert run_python("while True: pass", timeout_s=2)["status"] == "timeout"
    assert static_check("print('hi')") == []


def test_repl_output_is_capped():
    assert len(run_python("print('x'*100000)")["stdout"]) <= 4000
