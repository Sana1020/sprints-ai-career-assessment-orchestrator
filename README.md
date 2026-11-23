# Sprints Multi-Agent AI Career & Assessment Orchestrator

<p align="center">
  **An Intelligent Multi-Agent System for Learner Support, Python Assessment, and Career Guidance**
</p>

A LangGraph-powered multi-agent reference implementation designed to streamline learner support operations through curriculum question answering, automated Python assessment, learner profile retrieval, and human-in-the-loop placement recommendations.

The system coordinates specialized AI agents through a unified state graph, combines retrieval-augmented generation (RAG) with structured assessment, and uses database-backed learner information to support evidence-based career guidance.

---

## 1. Project Overview

The Sprints Multi-Agent AI Career & Assessment Orchestrator addresses three major operational challenges in large-scale AI bootcamps:

- Repetitive curriculum questions handled manually by student success teams.
- Time-consuming manual evaluation of Python assignments.
- Manual review of learner profiles and potential employer opportunities.

The solution introduces a coordinated multi-agent architecture built with **LangGraph, LangChain, ChromaDB, SQLite, and Pydantic**.

### Core Capabilities

| Capability | Description |
|---|---|
| Curriculum Advisor | Retrieves relevant learning materials and generates evidence-grounded answers |
| Python Assessor | Executes learner submissions and generates structured assessments |
| Evaluator-Optimizer | Reviews assessment results and supports iterative refinement |
| Learner Profile Agent | Retrieves learner information using read-only database tools |
| Placement Approval Gate | Pauses eligible placement workflows for human review |
| Session Management | Maintains conversation state using LangGraph checkpointing |
| Logging | Records workflow activity and message-style execution traces |

---

## 2. System Architecture

The system uses a unified **LangGraph StateGraph** to coordinate specialized agents and route incoming requests according to their intent.

### Main Components

| Component | Responsibility |
|---|---|
| LangGraph Orchestrator | Coordinates agents and controls workflow execution |
| Typed State | Maintains shared state across graph nodes |
| Advisor Agent | Retrieves curriculum information and evaluates evidence sufficiency |
| ChromaDB | Stores curriculum embeddings for semantic retrieval |
| Assessor Agent | Evaluates Python assignments |
| Evaluator-Optimizer | Supports assessment refinement, with a maximum of three iterations |
| Profile Agent | Retrieves learner information through database tools |
| SQLite Database | Stores learner records |
| Code Execution Tool | Runs Python submissions in a restricted subprocess |
| Placement Gate | Implements human approval using LangGraph interrupts |
| MemorySaver | Provides in-memory conversation checkpointing |

### Workflow Design

The orchestrator supports three main request paths:

1. **Curriculum Support:** Retrieve relevant documents, evaluate retrieval sufficiency, reformulate the query when necessary, and generate an evidence-grounded response.
2. **Python Assessment:** Execute the submitted code, generate a structured assessment, and apply the evaluator-optimizer workflow.
3. **Learner Profile and Placement:** Retrieve learner information from SQLite and pause eligible placement recommendations for human review.

### Advisor Self-Reflection Workflow

The advisor uses a conditional graph workflow:

`Retrieve → Reflect → Conditional Routing`

- If the retrieved context is sufficient, the graph proceeds to answer generation.
- If the context is insufficient, the query is reformulated and retrieval is repeated.
- The workflow allows up to three retrieval attempts before generating a response based on the available evidence.

This approach reduces unsupported answers when relevant curriculum information cannot be retrieved.

---

## 3. Technology Stack

| Technology | Usage |
|---|---|
| Python 3.11 | Core development language |
| LangGraph | Multi-agent orchestration and workflow management |
| LangChain | LLM integration and agent utilities |
| OpenAI API | Language model integration |
| ChromaDB | Vector storage and semantic retrieval |
| Sentence Transformers | Text embeddings |
| SQLite | Learner database |
| Pydantic | Structured assessment outputs |
| Pytest | Automated testing |
| Subprocess and AST | Restricted Python execution checks |

---

## 4. Project Structure

```text
sprints-ai-orchestrator/
│
├── data/
│   ├── curriculum_docs/
│   ├── chroma/
│   ├── sprints_learners.db
│   └── sprints_learner_db.example.csv
│
├── docs/
│   ├── project_charter.md
│   ├── technical_report.md
│   ├── technical_report.pdf
│   ├── final_presentation.pdf
│   ├── final_presentation.pptx
│   └── demo_script.md
│
├── notebooks/
│   └── evaluator_optimizer_loop.ipynb
│
├── src/
│   ├── agents/
│   │   ├── advisor_agent.py
│   │   ├── assessor_agent.py
│   │   ├── profile_agent.py
│   │   └── orchestrator.py
│   │
│   ├── tools/
│   │   ├── code_repl.py
│   │   ├── db_queries.py
│   │   └── rag_retriever.py
│   │
│   ├── config.py
│   ├── main.py
│   └── state.py
│
├── tests/
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 5. Installation and Configuration

### Requirements

- Python 3.11
- pip
- An OpenAI API key for live LLM operations

### Step 1: Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd sprints-ai-orchestrator
```

### Step 2: Create a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

**Windows:**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux:**

```bash
cp .env.example .env
```

Configure your `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
SPRINTS_MODEL=gpt-4o-mini
```

Never commit `.env` files or expose API credentials.

---

## 6. Data Preparation

### 6.1 Learner Database

The project includes a synthetic example dataset:

`data/sprints_learner_db.example.csv`

The example CSV contains three demonstration records.

For local development, a private dataset can be provided at:

`data/sprints_learner_db.csv`

When available, the database builder uses the local dataset to initialize the SQLite database.

Initialize the database:

```powershell
python -c "from src.tools.db_queries import build_database; print(build_database())"
```

The generated database is stored at:

`data/sprints_learners.db`

The database supports learner information such as:

- Learner ID
- Name
- Bootcamp track
- Completed modules
- Python assignment score
- Target salary (EGP)
- Preferred employers
- Readiness status

The local development database used during testing contained 25 learner records.

Private learner datasets should not be committed or distributed unless their use and sharing are explicitly authorized.

### 6.2 Curriculum Documents

Place curriculum documents in `.txt` or `.md` format under:

`data/curriculum_docs/`

Index the documents:

```powershell
python -c "from src.tools.rag_retriever import CurriculumRAG; print(CurriculumRAG().ingest())"
```

The current RAG pipeline uses:

- Character-based text splitting.
- Sentence Transformers embeddings: `sentence-transformers/all-MiniLM-L6-v2`.
- ChromaDB vector storage.
- Top-k retrieval: 4.

**Implementation note:** Exact 500-token chunk sizing and 50-token overlap are not verified in the current implementation. Tokenizer-aware splitting can be added as a further enhancement.

The included curriculum materials are demonstration content and should be replaced or supplemented with verified client curriculum documents before deployment.

---

## 7. Running the Application

The application supports curriculum questions, Python assessment requests, and learner-related queries through the command-line interface.

### 7.1 Curriculum Question

```powershell
python -m src.main --student-id SPR-1001 --thread-id curriculum-demo-001 --query "Explain LangGraph StateGraph and its main components."
```

### 7.2 Python Assessment

```powershell
python -m src.main --student-id SPR-1001 --thread-id assessment-demo-001 --query "Grade this factorial solution" --code "print(5*4*3*2*1)"
```

### 7.3 Learner Profile Request

```powershell
python -m src.main --student-id SPR-1001 --thread-id profile-demo-001 --query "What modules have I completed?"
```

Use a unique `thread_id` for each independent conversation.

Replace the sample learner ID with an ID available in your local database.

---

## 8. Python Assessment and Evaluator-Optimizer

The Assessor Agent evaluates Python submissions and generates structured results using Pydantic.

The assessment structure includes:

- `score`
- `feedback_points`
- `pass_status`

The evaluator-optimizer workflow supports iterative review and refinement, with a maximum of three assessment iterations.

The code execution component applies:

- AST-based code checks.
- Restricted subprocess execution.
- Execution timeout controls.

**Security limitation:** These controls provide basic execution restrictions, not a hardened security sandbox for hostile or untrusted code. Production deployment requires stronger process isolation and resource controls.

---

## 9. Human-in-the-Loop Placement Workflow

The placement workflow introduces a human approval gate for eligible Tier-1 placement recommendations.

LangGraph's `interrupt()` pauses execution and allows a human reviewer to make an explicit decision.

Supported decisions:

- `approved`
- `rejected`

The workflow can be resumed using the orchestrator's `approve_placement()` method.

The approval step is designed to prevent automatic progression without human review.

**Important:** Human approval does not confirm that an employer has an active vacancy or guarantee a successful placement. Employer matching must rely on verified and current database records.

---

## 10. Session Management and Logging

### Session Checkpointing

The orchestrator uses LangGraph `MemorySaver` with a unique `thread_id` to maintain conversation state across turns.

This supports continuity during an active application process.

**Production consideration:** `MemorySaver` is in-memory. Session state is not guaranteed to survive application restarts. A persistent database-backed checkpointer is recommended for production.

### Logging

The project includes logging configuration to record workflow activity and message-style execution traces.

Logging helps developers inspect routing behavior, workflow execution, and relevant agent activity during debugging and testing.

---

## 11. Testing and Validation

The project includes an automated offline test suite covering its main components.

Run the complete test suite:

```powershell
python -m pytest -q
```

### Test Coverage

- Advisor retrieval and response behavior.
- Advisor self-reflection and conditional graph routing.
- Structured assessment generation.
- Evaluator-optimizer workflow.
- Restricted Python code execution.
- SQLite database tools and read-only query behavior.
- Learner profile retrieval.
- Orchestrator routing and workflow execution.
- Message-style logging traces.
- Offline integration and tool behavior.

### Latest Recorded Test Results

| Validation | Result |
|---|---|
| Full automated test suite | 27 passed |
| Logging trace test | 1 passed |
| Local learner database check | 25 records |
| Learner profile lookup | Successful |
| Live OpenAI API execution | Not validated in the latest run |

The recorded test results demonstrate successful offline validation of the tested components. Live LLM workflows still require an available API key and sufficient API quota.

---

## 12. Implementation Status and Limitations

The core reference implementation includes the multi-agent orchestration workflow, conditional advisor reflection, structured Python assessment, learner profile tools, session checkpointing, and human approval gate.

The following items remain important deployment considerations:

| Area | Current Status |
|---|---|
| LangGraph multi-agent orchestration | Implemented |
| Typed shared state | Implemented |
| Conditional advisor self-reflection | Implemented |
| ChromaDB curriculum retrieval | Implemented |
| Exact 500-token chunking | Not yet verified |
| Pydantic structured assessment | Implemented |
| Evaluator-optimizer iteration limit | Implemented |
| Read-only SQLite learner tools | Implemented |
| Restricted Python execution | Implemented; not production-hardened |
| Human-in-the-loop placement gate | Implemented |
| In-memory session checkpointing | Implemented |
| Persistent production checkpointing | Future enhancement |
| Offline automated tests | 27 tests passed |
| Live API end-to-end validation | Pending |

These limitations distinguish the validated reference implementation from a production deployment and identify the next engineering steps.

---

## 13. Future Enhancements

Potential improvements include:

- Implement tokenizer-aware 500-token chunking with 50-token overlap.
- Add persistent LangGraph checkpoint storage.
- Strengthen Python execution isolation.
- Add authenticated human approval interfaces and audit trails.
- Integrate verified, up-to-date employer vacancy data.
- Add PDF and DOCX curriculum ingestion.
- Expand evaluation datasets and measure retrieval quality.
- Conduct live API end-to-end testing.
- Add monitoring, performance metrics, and deployment automation.

---

## 14. Project Deliverables

The project submission includes:

- Multi-agent application source code.
- LangGraph orchestration and shared state implementation.
- Curriculum RAG components and sample documents.
- Python assessment and evaluator-optimizer workflow.
- SQLite learner database tooling.
- Human-in-the-loop placement workflow.
- Automated offline test suite.
- Technical documentation.
- Project presentation.
- Demonstration recording.

---

## 15. Conclusion

The Sprints Multi-Agent AI Career & Assessment Orchestrator brings together specialized AI workers in a unified, stateful workflow.

By combining curriculum retrieval, structured Python assessment, learner profile analysis, and human-supervised placement decisions, the project demonstrates how agentic AI can support learner success operations in a scalable bootcamp environment.

The implementation establishes a foundation for more reliable learner support, reduced repetitive manual work, and evidence-based career guidance, while clearly identifying the additional validation and security measures required for production deployment.
---
### Project Summary
- **Project:** Sprints Multi-Agent AI Career & Assessment Orchestrator
- **Architecture:** LangGraph Multi-Agent StateGraph
- **Validation:** 27 Offline Tests Passed
- **Status:** Core Reference Implementation Completed