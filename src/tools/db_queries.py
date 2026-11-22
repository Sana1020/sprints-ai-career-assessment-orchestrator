
"""Read-only learner database tools with structured failure handling."""

import csv
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from langchain_core.tools import tool
from src.config import UNABLE_TO_VERIFY


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "sprints_learners.db"
PRIVATE_CSV_PATH = PROJECT_ROOT / "data" / "sprints_learner_db.csv"
EXAMPLE_CSV_PATH = PROJECT_ROOT / "data" / "sprints_learner_db.example.csv"


def build_database(force=False, csv_path=None, db_path=DB_PATH):
    """Create or refresh the SQLite learners table from the supplied CSV."""

    if csv_path is None:
        csv_path = (
            PRIVATE_CSV_PATH
            if PRIVATE_CSV_PATH.exists()
            else EXAMPLE_CSV_PATH
        )

    csv_path = Path(csv_path)
    db_path = Path(db_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames

        if not columns:
            raise ValueError("CSV has no column headers")

        records = list(reader)

    integer_columns = {
        "completed_modules",
        "python_assignment_score",
        "target_salary_egp",
    }

    definitions = []
    for column in columns:
        safe_column = column.replace('"', '""')
        sql_type = "INTEGER" if column in integer_columns else "TEXT"
        definitions.append(f'"{safe_column}" {sql_type}')

    create_sql = (
        "CREATE TABLE IF NOT EXISTS learners ("
        + ", ".join(definitions)
        + ")"
    )

    placeholders = ", ".join("?" for _ in columns)
    quoted_columns = ", ".join(
        f'"{column.replace(chr(34), chr(34) * 2)}"'
        for column in columns
    )

    insert_sql = (
        f"INSERT INTO learners ({quoted_columns}) "
        f"VALUES ({placeholders})"
    )

    # Ensure the SQLite connection is closed after the transaction.
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            if force:
                connection.execute("DROP TABLE IF EXISTS learners")

            connection.execute(create_sql)

            existing = connection.execute(
                "SELECT COUNT(*) FROM learners"
            ).fetchone()[0]

            if force or existing == 0:
                connection.execute("DELETE FROM learners")

                values = []
                for record in records:
                    row = []
                    for column in columns:
                        value = record.get(column)
                        if column in integer_columns and value not in (None, ""):
                            value = int(value)
                        row.append(value)
                    values.append(tuple(row))

                connection.executemany(insert_sql, values)

    return {
        "status": "ok",
        "rows_imported": len(records),
        "columns": columns,
        "database": str(db_path),
    }


def _readonly_connection(db_path):
    """Open an existing SQLite database in read-only mode."""
    path = Path(db_path).resolve()
    uri = path.as_uri() + "?mode=ro"

    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def get_learner_profile(student_id: str) -> dict:
    """Retrieve a learner profile using an exact learner ID."""
    try:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", student_id or ""):
            return {
                "status": UNABLE_TO_VERIFY,
                "reason": "Invalid learner ID",
                "rows": [],
            }

        # closing() guarantees that the read-only connection is released.
        with closing(_readonly_connection(DB_PATH)) as connection:
            rows = connection.execute(
                "SELECT * FROM learners WHERE learner_id = ? LIMIT 1",
                (student_id,),
            ).fetchall()

        if not rows:
            return {
                "status": UNABLE_TO_VERIFY,
                "reason": "Learner not found",
                "rows": [],
            }

        result_rows = [dict(row) for row in rows]

        return {
            "status": "ok",
            "rows": result_rows,
            "learner": result_rows[0],
        }

    except Exception as exc:
        return {
            "status": UNABLE_TO_VERIFY,
            "reason": f"Database error: {type(exc).__name__}",
            "rows": [],
        }


def run_readonly_query(query: str, db_path: str = str(DB_PATH)) -> dict:
    """Execute one read-only SELECT query and return structured results."""
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Empty SQL query")

        first_word = re.match(r"\s*([A-Za-z]+)", query)
        if not first_word or first_word.group(1).upper() not in {"SELECT", "WITH"}:
            raise ValueError("Only SELECT queries are allowed")

        connection = _readonly_connection(db_path)

        write_actions = {
            sqlite3.SQLITE_INSERT,
            sqlite3.SQLITE_UPDATE,
            sqlite3.SQLITE_DELETE,
            sqlite3.SQLITE_CREATE_INDEX,
            sqlite3.SQLITE_CREATE_TABLE,
            sqlite3.SQLITE_CREATE_TRIGGER,
            sqlite3.SQLITE_CREATE_VIEW,
            sqlite3.SQLITE_DROP_INDEX,
            sqlite3.SQLITE_DROP_TABLE,
            sqlite3.SQLITE_DROP_TRIGGER,
            sqlite3.SQLITE_DROP_VIEW,
            sqlite3.SQLITE_ALTER_TABLE,
            sqlite3.SQLITE_ATTACH,
            sqlite3.SQLITE_DETACH,
        }

        def authorizer(action, arg1, arg2, database, trigger):
            if action in write_actions:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        connection.set_authorizer(authorizer)

        try:
            cursor = connection.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
            columns = [item[0] for item in cursor.description or []]
        finally:
            connection.close()

        return {
            "status": "ok",
            "rows": rows,
            "columns": columns,
        }

    except Exception as exc:
        return {
            "status": UNABLE_TO_VERIFY,
            "reason": f"Query failed: {type(exc).__name__}",
            "rows": [],
        }


@tool
def get_learner_profile_tool(student_id: str) -> dict:
    """LangChain tool for retrieving a learner profile."""
    return get_learner_profile(student_id)


@tool
def run_readonly_query_tool(query: str) -> dict:
    """LangChain tool for executing a read-only learner database query."""
    return run_readonly_query(query)
