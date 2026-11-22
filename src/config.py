"""Shared constants and helpers for the Sprints AI Orchestrator.

Kept dependency-free (stdlib only) so the SQL tool and the Python sandbox can be
unit-tested without LangChain/LangGraph installed.

Curriculum mapping: Sprint 1 (foundations: configuration, logging, fallbacks)
and Sprint 2 (shared limits for the LangGraph loops).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
CURRICULUM_DIR = DATA_DIR / "curriculum_docs"
CSV_PATH = DATA_DIR / "sprints_learner_db.csv"
DB_PATH = DATA_DIR / "sprints_learner_db.sqlite"
CHROMA_DIR = ROOT / "chroma_store"

# --- RAG configuration (Sprint 1, brief: 500-token chunks, 50-token overlap) ---
CHUNK_SIZE_TOKENS = 500
CHUNK_OVERLAP_TOKENS = 50
RETRIEVAL_BUDGET_MS = 1000          # acceptance criterion: retrieval < 1000 ms
RETRIEVAL_TOP_K = 4
MAX_QUERY_REFORMULATIONS = 2        # self-reflection loop bound (Sprint 2)

# --- Assessor configuration ---
MAX_REFINEMENTS = 3                 # acceptance criterion: halt after 3 refinements
PASS_MARK = 70
SANDBOX_TIMEOUT_S = 5

# --- Placement / HITL ---
TIER1_PARTNERS = frozenset({"fawry"})   # lower-case; add more tier-1 partners here

UNABLE_TO_VERIFY = "Unable to verify"


def unable_to_verify(tool: str, reason: str) -> dict:
    """Structured graceful-fallback payload returned when a tool raises.

    Curriculum link: Sprint 1 (tool error handling) - used by the SQL tool, the
    Python sandbox and the retriever so the orchestrator never crashes.
    """
    return {"status": UNABLE_TO_VERIFY, "tool": tool, "reason": reason}


def configure_logging(verbose: bool = True) -> None:
    """Enable verbose protocol logs (HumanMessage / AIMessage / ToolMessage)."""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def get_llm(temperature: float = 0.0):
    """Return the chat model used by every agent (OpenAI API)."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=os.getenv("SPRINTS_MODEL", "gpt-4o-mini"), temperature=temperature)


def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )