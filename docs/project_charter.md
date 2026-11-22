
# Project Charter — Sprints Multi-Agent AI Career & Assessment Orchestrator

**Status:** Draft based on the written brief and reviewed kickoff deck. Discovery-call MP3 was not available in the working attachments.

## Problem
As Sprints scales employer-connected technology bootcamps, human advisors and technical graders risk becoming bottlenecks. Learners need timely curriculum answers, consistent Python feedback, and visibility into their progress and career preferences.

## Goal
Deliver a stateful, multi-agent workflow that routes learner requests to specialist workers, grounds curriculum answers in Sprints documents, executes bounded Python checks, retrieves learner profile data, and pauses tier-1 placement recommendations for human approval.

## In scope
- Curriculum ingestion, chunking, embeddings, ChromaDB retrieval.
- Pydantic structured assessment output.
- Read-only SQLite learner profile lookup.
- Bounded Python execution and error capture.
- LangGraph routing, per-thread state, RAG self-reflection, evaluator-optimizer loop.
- HITL approval gate for tier-1 partners.
- Technical report, stakeholder deck, notebook, README and demo plan.

## Success criteria
- Each of the three request classes routes to the intended worker.
- Curriculum answers cite/identify indexed source material and abstain when evidence is insufficient.
- Assessment returns score, feedback points, pass status and execution status.
- DB/runner failures return `Unable to verify` rather than fabricated data.
- Refinement stops after at most three iterations.
- A tier-1 placement request pauses until an explicit human decision is supplied.
- Retrieval latency is measured on the real corpus; target <1000 ms.

## Risks and mitigations
| Risk | Mitigation |
|---|---|
| Unavailable or inconsistent source assets | Confirm deck, transcript, curriculum and CSV schema before acceptance |
| Unsafe execution of learner code | Isolated container/VM; current subprocess runner is demo-only |
| Incorrect grading | Rubric, hidden tests, judge review, human audit |
| Incorrect profile lookup | Read-only DB, parameterized values, schema validation |
| False placement confidence | Mandatory human approval; never auto-finalize tier-1 placements |
| Latency and API limits | Cache embeddings, benchmark retrieval, bounded retries |

## Assumptions and open questions
- OpenAI API credentials and approved model access are available.
- Client permits processing curriculum and learner data through selected services.
- The supplied CSV has learner_id and profile fields; no job-vacancy table is included.
- Definition of “tier-1 partner” and placement approval authority must be confirmed.
- Tokenizer, file formats, grading rubric, pass threshold and retention policy require stakeholder confirmation.
