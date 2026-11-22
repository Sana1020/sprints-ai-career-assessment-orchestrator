
"""Tests for curriculum RAG retrieval and latency."""

from src.tools.rag_retriever import CurriculumRAG


def test_rag_retrieves_relevant_curriculum_documents():
    rag = CurriculumRAG()

    docs, latency = rag.retrieve(
        "How does Evaluator Optimizer improve an AI agent answer?"
    )

    assert len(docs) > 0

    content = " ".join(
        doc.page_content.lower() for doc in docs
    )

    assert "evaluator" in content or "optimizer" in content


def test_rag_retrieval_latency_under_one_second():
    rag = CurriculumRAG()

    docs, latency = rag.retrieve(
        "Explain LangGraph StateGraph and nodes."
    )

    assert len(docs) > 0
    assert latency < 1000
