
"""LangGraph orchestrator for the Sprints AI Career and Assessment system."""

from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

from src.state import SprintsState
from src.agents.advisor_agent import AdvisorAgent
from src.agents.assessor_agent import AssessorAgent
from src.agents.profile_agent import ProfileAgent
from src.tools.db_queries import get_learner_profile_tool


class SprintsOrchestrator:
    """Route learner requests and manage agent workflows with HITL."""

    def __init__(
        self,
        llm=None,
        advisor=None,
        assessor=None,
        profile_agent=None,
    ):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )

        self.advisor = advisor or AdvisorAgent()
        self.assessor = assessor or AssessorAgent()
        self.profile_agent = profile_agent or ProfileAgent()

        graph = StateGraph(SprintsState)

        graph.add_node("router", self.router)
        graph.add_node("advisor", self.advisor_node)
        graph.add_node("assessor", self.assessor_node)
        graph.add_node("profile", self.profile_node)
        graph.add_node("placement_gate", self.placement_gate)
        graph.add_node("finish", self.finish_node)

        graph.add_edge(START, "router")

        graph.add_conditional_edges(
            "router",
            self.route,
            {
                "advisor": "advisor",
                "assessor": "assessor",
                "profile": "profile",
            },
        )

        graph.add_edge("advisor", "finish")
        graph.add_edge("assessor", "finish")
        graph.add_edge("profile", "placement_gate")
        graph.add_edge("placement_gate", "finish")
        graph.add_edge("finish", END)

        self.app = graph.compile(checkpointer=MemorySaver())

    def router(self, state):
        """Classify the learner request into one of three intents."""

        label = self.llm.invoke(
            "Classify as exactly advisor, assessor, or profile. "
            "Code submission or grading => assessor; "
            "salary, progress, employer, or placement => profile.\n"
            + state.get("query", "")
        ).content.strip().lower()

        if label not in {"advisor", "assessor", "profile"}:
            label = "advisor"

        return {"intent": label}

    def route(self, state) -> Literal["advisor", "assessor", "profile"]:
        """Select the graph route."""

        return state["intent"]

    def advisor_node(self, state):
        """Answer curriculum questions using RAG."""

        try:
            result = self.advisor.answer(state["query"])

            answer = result.get(
                "answer",
                "Unable to verify from the provided curriculum.",
            )

            return {
                "answer": answer,
                "retrieved_context": result.get("context", ""),
                "retrieval_ms": result.get("retrieval_ms", 0.0),
                "messages": [AIMessage(content=str(answer))],
            }

        except Exception as exc:
            answer = (
                "Unable to verify curriculum information. "
                f"Reason: {type(exc).__name__}"
            )

            return {
                "answer": answer,
                "error": str(exc),
                "messages": [AIMessage(content=answer)],
            }

    def assessor_node(self, state):
        """Execute and assess a learner Python submission."""

        try:
            result = self.assessor.assess(
                state["query"],
                state.get("code", ""),
            )

            answer = str(result)

            return {
                "assessment": result,
                "answer": answer,
                "messages": [AIMessage(content=answer)],
            }

        except Exception as exc:
            answer = (
                "Unable to verify the code assessment. "
                f"Reason: {type(exc).__name__}"
            )

            return {
                "assessment": {
                    "status": "Unable to verify",
                    "reason": type(exc).__name__,
                },
                "answer": answer,
                "error": str(exc),
                "messages": [AIMessage(content=answer)],
            }

    def profile_node(self, state):
        """Retrieve learner information and prepare placement review."""

        student_id = state.get("student_id", "")

        try:
            agent_result = self.profile_agent.answer(
                f"Student ID: {student_id}\n"
                f"Learner question: {state.get('query', '')}"
            )

            profile = get_learner_profile_tool.invoke({
                "student_id": student_id
            })

            if not isinstance(profile, dict):
                raise ValueError("Invalid learner profile response")

            if profile.get("status") != "ok":
                raise ValueError("Learner profile could not be verified")

            if agent_result.get("status") != "ok":
                raise ValueError("Profile agent could not verify the answer")

            answer = agent_result.get(
                "answer",
                "Unable to verify learner information.",
            )

            profile["agent_answer"] = answer

            return {
                "learner_profile": profile,
                "answer": answer,
                "messages": [AIMessage(content=answer)],
            }

        except Exception as exc:
            answer = (
                "Unable to verify learner profile. "
                "Placement cannot proceed."
            )

            return {
                "learner_profile": {
                    "status": "Unable to verify",
                    "rows": [],
                },
                "answer": answer,
                "error": str(exc),
                "messages": [AIMessage(content=answer)],
            }

    def placement_gate(self, state):
        """Require human approval before a Tier-1 placement proceeds."""

        profile = state.get("learner_profile", {})

        if profile.get("status") != "ok":
            answer = (
                "Unable to verify learner profile. "
                "Placement cannot proceed."
            )

            return {
                "answer": answer,
                "needs_human_approval": False,
                "messages": [AIMessage(content=answer)],
            }

        learner = profile.get("learner", {})

        preferred_employers = str(
            learner.get("preferred_employers", "")
        ).lower()

        query = state.get("query", "").lower()

        tier1 = (
            "fawry" in preferred_employers
            or "fawry" in query
        )

        if not tier1:
            answer = (
                "Learner profile retrieved successfully. "
                "No Tier-1 approval required."
            )

            return {
                "answer": answer,
                "needs_human_approval": False,
                "messages": [AIMessage(content=answer)],
            }

        decision = interrupt({
            "type": "placement_approval_required",
            "message": (
                "Fawry is a Tier-1 partner. "
                "Human approval is required before proceeding."
            ),
            "student_id": state.get("student_id"),
            "profile": profile,
        })

        approved = str(decision).strip().lower() in {
            "approve",
            "approved",
            "yes",
            "true",
        }

        if approved:
            answer = "Human review approved. Placement may proceed."

            return {
                "human_decision": "approved",
                "needs_human_approval": False,
                "placement": {
                    "status": "approved",
                    "partner": "Fawry",
                },
                "answer": answer,
                "messages": [AIMessage(content=answer)],
            }

        answer = "Human review rejected. Placement must not proceed."

        return {
            "human_decision": "rejected",
            "needs_human_approval": False,
            "placement": {
                "status": "rejected",
                "partner": "Fawry",
            },
            "answer": answer,
            "messages": [AIMessage(content=answer)],
        }

    def finish_node(self, state):
        """Preserve accumulated messages and final answer."""

        return {
            "answer": state.get("answer", "Unable to verify"),
        }

    def invoke(self, query, student_id, thread_id, code=""):
        """Run the graph using a persistent thread identifier."""

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        return self.app.invoke(
            {
                "query": query,
                "student_id": student_id,
                "thread_id": thread_id,
                "code": code,
                "messages": [HumanMessage(content=query)],
            },
            config=config,
        )

    def approve_placement(self, decision, thread_id):
        """Resume a paused graph after a human decision."""

        return self.app.invoke(
            Command(resume=decision),
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )
