
"""RAG-powered curriculum advisor with one self-reflection retry."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.tools.rag_retriever import CurriculumRAG


class AdvisorAgent:
    """Answer learner questions using retrieved curriculum evidence."""

    def __init__(self, llm=None, rag=None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.rag = rag or CurriculumRAG()

    def _format_context(self, docs):
        """Include source filenames alongside retrieved document content."""
        if not docs:
            return ""

        return "\n\n".join(
            f"Source: {doc.metadata.get('source_file', doc.metadata.get('source', 'Unknown'))}\n"
            f"Content:\n{doc.page_content}"
            for doc in docs
        )

    def answer(self, question: str):
        """Retrieve evidence, retry once if insufficient, then generate an answer."""

        docs, latency = self.rag.retrieve(question)
        context = self._format_context(docs)

        sufficiency = self.llm.invoke([
            SystemMessage(content=(
                "Determine whether the supplied context contains enough "
                "relevant evidence to answer the question. "
                "Reply with exactly YES or NO."
            )),
            HumanMessage(content=f"Question: {question}\nContext:\n{context}")
        ]).content.strip().upper()

        if sufficiency != "YES":
            rewritten = self.llm.invoke([
                SystemMessage(content=(
                    "Rewrite the learner's question as a concise "
                    "search query for the Sprints curriculum."
                )),
                HumanMessage(content=question)
            ]).content.strip()

            docs2, latency2 = self.rag.retrieve(rewritten)
            docs = docs2
            latency += latency2
            context = self._format_context(docs)

        result = self.llm.invoke([
            SystemMessage(content=(
                "You are the Sprints curriculum advisor. "
                "Answer clearly and concisely using ONLY the supplied context. "
                "Never invent information. "
                "If the context does not contain enough evidence, reply: "
                "'Unable to verify from the provided curriculum'. "
                "Mention the source filenames used in your answer."
            )),
            HumanMessage(content=f"Question: {question}\nContext:\n{context}")
        ]).content

        return {
            "answer": result,
            "context": context,
            "retrieval_ms": round(latency, 2)
        }
