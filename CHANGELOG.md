# Changelog of decisions
- **Router = regex + LLM.** Code blocks and learner ids are extracted deterministically; the LLM only classifies intent (cheaper, more reliable).
- **Three intents on two worker agents.** Curriculum Q&A and career matching both live in the Advisor; grading in the Assessor (matches the brief's tree and the call's three-task framing).
- **Own sandbox instead of langchain_experimental PythonREPL**, which executes in-process with full privileges.
- **Grounded RAG.** If context stays insufficient after 2 reformulations the agent says it is not in the curriculum.
- **pass_status derived from score in code** (>= 70) so the schema can never be inconsistent; the judge still reviews it.
- **Refinement cap = 3** enforced in `route_after_judge` (max 4 grading passes in total).
- **HITL via `interrupt`**, resumed with `Command(resume=...)` on the same per-student thread.
- **Judge failure fails open** (returns the grade) so a broken judge never blocks a learner.
