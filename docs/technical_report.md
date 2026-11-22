
# Technical Report
## Sprints Multi-Agent AI Career & Assessment Orchestrator

### Executive summary
This implementation provides a LangGraph orchestration skeleton for three learner workflows: curriculum advising, Python assessment, and learner-profile/placement support. The design separates routing from specialist workers and uses structured outputs and a human approval pause for tier-1 placements.

### Architecture
The graph begins with a router node that classifies each request. Advisor requests enter a RAG worker; code submissions enter an assessor worker; progress, salary, employer, and placement requests enter a read-only profile worker. Profile results pass through a placement gate. If Fawry is implicated, LangGraph `interrupt()` pauses execution for an explicit human decision. The graph is compiled with `MemorySaver`, keyed by a unique thread ID.

### RAG configuration
Curriculum files are loaded from `data/curriculum_docs`, split, embedded with `text-embedding-3-small`, and persisted in ChromaDB. Retrieval returns source documents and a measured latency. An evidence sufficiency check decides whether to reformulate and retrieve once more. The response prompt instructs the advisor to abstain when context is insufficient.

The splitter uses `tiktoken` with the `cl100k_base` encoding, a 500-token target, and 50-token overlap. Validate the resulting chunks against the client corpus and embedding model during acceptance testing.

### Assessment and evaluator-optimizer
The assessor executes a submission with a bounded subprocess runner, then requests a Pydantic `Assessment` containing score, feedback points, pass status and execution status. A second LLM reviews the result against a rubric. The loop has a strict maximum of three iterations.

Successful execution is not treated as proof of correctness. Production grading should add hidden unit tests, expected-output comparisons, plagiarism policy, and human sampling.

### Database strategy
The profile tool opens SQLite in read-only mode, uses parameterized values, and returns a structured `Unable to verify` response on errors. The CSV import normalizes column names, but the client schema must be inspected and mapped before production use. The included rows are synthetic demonstration data.

### Memory strategy
`MemorySaver` provides thread-scoped graph checkpointing for a single-process demonstration. Each learner conversation must use a stable unique thread ID. For deployment across workers or restarts, use a persistent checkpointer such as PostgreSQL and define retention, deletion, and access policies.

### Human oversight
A tier-1 partner recommendation pauses through LangGraph `interrupt()`. An authorized reviewer must resume with an explicit approval or rejection. The demo gate recognizes Fawry by name; production requires a maintained partner tier registry, reviewer authentication, audit trail, and separation of duties.

### Security and privacy
The example code runner is not a hostile-code sandbox. AST checks and subprocess timeouts are insufficient against all escape techniques. Production must execute code in disposable, network-disabled containers or microVMs with CPU, memory, process and filesystem limits. Learner data must be minimized, access-controlled, encrypted, and retained only under an approved policy.

### Validation plan
1. Run unit tests for safe output capture, blocked imports and timeouts.
2. Test advisor questions against known curriculum passages and unsupported questions.
3. Test CSV import, missing student, malformed schema and DB outage.
4. Test correct, incorrect, runtime-error and timeout Python submissions.
5. Test evaluator loop count never exceeds three.
6. Test separate thread IDs do not share state.
7. Test Fawry placement pause, approval, rejection and non-tier-1 bypass.
8. Benchmark warm and cold Chroma retrieval on the real curriculum corpus; report p50/p95.

### Current limitations and evidence status
The kickoff deck and supplied 25-row mock learner CSV were available and used; the SQLite database was generated from that CSV. The discovery MP3 was not available in the working attachments. The supplied CSV is assignment mock data, not live production data. It does not include live job openings or job requirements. No claim is made that the 1000 ms retrieval target, exact token chunking, production-grade sandboxing, or full end-to-end acceptance tests have been achieved.
