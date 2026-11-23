
"""Typed state shared by Sprints orchestration workers."""

from typing import TypedDict, Optional, Annotated, Any
from langgraph.graph.message import add_messages


class SprintsState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes."""

    # Learner and conversation information
    student_id: str
    thread_id: str
    messages: Annotated[list, add_messages]
    query: str
    code: str

    # Routing
    intent: str

    # Agent outputs
    answer: str
    assessment: dict
    learner_profile: dict
    retrieved_context: str
    retrieval_ms: float

    # Advisor self-reflection workflow
    advisor_query: str
    advisor_docs: list[Any]
    advisor_context: str
    advisor_sufficient: bool
    advisor_retry_count: int

    # Placement and human approval
    placement: dict
    needs_human_approval: bool
    human_decision: Optional[str]

    # Execution and error handling
    retry_count: int
    error: Optional[str]
