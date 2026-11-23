
"""RAG-powered curriculum advisor with graph-compatible reflection steps."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.tools.rag_retriever import CurriculumRAG


class AdvisorAgent:
    """Answer learner questions using retrieved curriculum evidence."""

    def __init__(self, llm=None, rag=None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )
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

    def retrieve(self, question: str):
        """Retrieve relevant curriculum documents."""

        docs, latency = self.rag.retrieve(question)

        return {
            "advisor_docs": docs,
            "advisor_context": self._format_context(docs),
            "retrieval_ms": round(latency, 2),
        }

    def reflect(self, question: str, context: str) -> bool:
        """Evaluate whether retrieved evidence is sufficient."""

        response = self.llm.invoke([
            SystemMessage(content=(
                "Determine whether the supplied context contains enough "
                "relevant evidence to answer the question. "
                "Reply with exactly YES or NO."
            )),
            HumanMessage(
                content=f"Question: {question}\nContext:\n{context}"
            ),
        ]).content.strip().upper()

        return response == "YES"

    def rewrite_query(self, question: str) -> str:
        """Rewrite the learner question into a curriculum search query."""

        response = self.llm.invoke([
            SystemMessage(content=(
                "Rewrite the learner's question as a concise "
                "search query for the Sprints curriculum."
            )),
            HumanMessage(content=question),
        ]).content.strip()

        return response or question

    def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using only retrieved curriculum evidence."""

        return self.llm.invoke([
            SystemMessage(content=(
                "You are the Sprints curriculum advisor. "
                "Answer clearly and concisely using ONLY the supplied context. "
                "Never invent information. "
                "If the context does not contain enough evidence, reply: "
                "'Unable to verify from the provided curriculum'. "
                "Mention the source filenames used in your answer."
            )),
            HumanMessage(
                content=f"Question: {question}\nContext:\n{context}"
            ),
        ]).content

    def answer(self, question: str):
        """Backward-compatible standalone workflow with one retry."""

        retrieval = self.retrieve(question)
        docs = retrieval["advisor_docs"]
        context = retrieval["advisor_context"]
        latency = retrieval["retrieval_ms"]

        sufficient = self.reflect(question, context)

        if not sufficient:
            rewritten = self.rewrite_query(question)

            retrieval = self.retrieve(rewritten)
            docs = retrieval["advisor_docs"]
            context = retrieval["advisor_context"]
            latency += retrieval["retrieval_ms"]

        result = self.generate_answer(question, context)

        return {
            "answer": result,
            "context": context,
            "retrieval_ms": round(latency, 2),
        }
