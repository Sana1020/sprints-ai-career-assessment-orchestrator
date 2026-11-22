
"""Agent for read-only learner profile and SQL queries."""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src.tools.db_queries import (
    get_learner_profile_tool,
    run_readonly_query_tool,
)


SYSTEM_PROMPT = """
You are the Sprints learner profile assistant.

Your job is to answer questions about:
- Learner information
- Completed modules
- Python assignment scores
- Target salary
- Preferred employers
- Learner readiness

You have two tools:
1. get_learner_profile_tool: retrieve a learner using an exact student ID.
2. run_readonly_query_tool: execute read-only SQL queries.

Rules:
- Always use tools to retrieve learner-specific information.
- Use the exact student ID provided by the user.
- Use SQL SELECT queries only.
- Never invent learner data or query results.
- If a tool returns "Unable to verify", explain that the information
  could not be verified.
- Do not claim that real job vacancies or placement matches exist.
- Answer clearly and concisely.
"""


class ProfileAgent:
    """Answer learner profile questions using a tool-calling agent."""

    def __init__(self, llm=None, agent=None):
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )

        self.tools = [
            get_learner_profile_tool,
            run_readonly_query_tool,
        ]

        self.agent = agent if agent is not None else create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=SYSTEM_PROMPT,
        )

    
    def answer(self, question: str) -> dict:
        """Run the agent and return its final answer."""

        try:
            result = self.agent.invoke({
                "messages": [("user", question)]
            })

            messages = result.get("messages", [])

            if not messages:
                return {
                    "status": "Unable to verify",
                    "answer": "Unable to verify learner information.",
                    "messages": [],
                }

            answer = messages[-1].content

            if not isinstance(answer, str) or not answer.strip():
                return {
                    "status": "Unable to verify",
                    "answer": "Unable to verify learner information.",
                    "messages": messages,
                }

            return {
                "status": "ok",
                "answer": answer,
                "messages": messages,
            }

        except Exception as exc:
            return {
                "status": "Unable to verify",
                "answer": (
                    "Unable to verify learner information. "
                    f"Reason: {type(exc).__name__}"
                ),
                "messages": [],
            }
