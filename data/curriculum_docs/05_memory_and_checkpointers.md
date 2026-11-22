# Memory and Checkpointers (Sprint 2)
A checkpointer saves the graph state after every step. MemorySaver keeps checkpoints in memory and is suitable for development; production systems use a database-backed checkpointer. Each conversation is identified by a `thread_id` passed in the config. Using one thread per student isolates their histories and prevents context amnesia between turns, while ensuring one learner never sees another learner's messages.
Checkpointing is also what makes human-in-the-loop possible: a paused graph can be resumed later from its saved state.
