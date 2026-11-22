# Human-in-the-Loop with interrupt (Sprint 2)
High-stakes decisions need human oversight. LangGraph's `interrupt` primitive pauses execution inside a node and surfaces a payload to the caller. The graph stays paused, with its state saved by the checkpointer, until the caller resumes it with `Command(resume=value)`. At Sprints, every job placement recommendation for a tier-1 partner such as Fawry is paused for approval by a human expert before it reaches the learner.
Code before an `interrupt` call re-runs when the graph resumes, so it must be free of side effects.
