# Sprints Multi-Agent AI Career & Assessment Orchestrator

A LangGraph-based multi-agent reference implementation for curriculum Q&A, Python code assessment, learner-profile lookup, and human-in-the-loop placement recommendations.

## 1. Project Overview

The system contains four main workers coordinated through a LangGraph StateGraph:

- **Advisor Agent:** Retrieves relevant curriculum content from ChromaDB and answers questions using retrieved evidence.
- **Assessor Agent:** Executes Python submissions, generates structured Pydantic assessments, and applies an evaluator-optimizer loop with a maximum of three iterations.
- **Profile Agent:** Uses read-only database tools to retrieve learner information and answer profile-related questions.
- **Placement Gate:** Applies a human-in-the-loop approval step before proceeding with eligible Tier-1 placement recommendations.

The graph uses `MemorySaver` to preserve conversation state using a unique `thread_id`.

## 2. Architecture

| Component | Responsibility |
|---|---|
| LangGraph Router | Routes requests to Advisor, Assessor, or Profile |
| Advisor | Curriculum retrieval, evidence sufficiency check, and query reformulation |
| ChromaDB | Vector storage and semantic curriculum retrieval |
| Assessor | Python execution and structured assessment |
| Evaluator-Optimizer | Reviews and refines assessments, up to 3 iterations |
| Profile Agent | Tool-calling agent for learner information and read-only SQL |
| SQLite | Stores learner records |
| Code REPL | Executes learner code in a restricted subprocess |
| Placement Gate | Pauses for human approval using LangGraph `interrupt()` |
| MemorySaver | Maintains graph state across turns using `thread_id` |

## 3. Project Requirements

- Python 3.11
- OpenAI API key for live LLM operations
- Dependencies listed in `requirements.txt`

## 4. Installation

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create your environment file:

**Windows:**

```powershell
Copy-Item .env.example .env
```

**macOS/Linux:**

```bash
cp .env.example .env
```

Add your API key to `.env`:

```env
OPENAI_API_KEY=your_api_key_here
SPRINTS_MODEL=gpt-4o-mini
```

Do not commit `.env` or expose API keys in the repository.

## 5. Data Preparation

### 5.1 Learner Database

The repository includes a synthetic example dataset:

`data/sprints_learner_db.example.csv`

It contains 3 demo learner records and is intended for testing and demonstration only.

If a private dataset named `data/sprints_learner_db.csv` exists locally, the database builder uses it instead. This private file is excluded from Git.

Initialize the SQLite database:

```powershell
python -c "from src.tools.db_queries import build_database; print(build_database())"
```

The database is created at:

`data/sprints_learners.db`

The database includes learner information such as:

- Learner ID
- Name
- Bootcamp track
- Completed modules
- Python assignment score
- Target salary (EGP)
- Preferred employers
- Readiness status

The database is generated locally and is not committed to the repository.

### 5.2 Curriculum Documents

Add curriculum documents in `.txt` or `.md` format under:

`data/curriculum_docs/`

Index the documents:

```powershell
python -c "from src.tools.rag_retriever import CurriculumRAG; print(CurriculumRAG().ingest())"
```

The RAG pipeline uses:

- Tokenizer-aware text splitting
- Chunk size: 500 tokens
- Chunk overlap: 50 tokens
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Vector database: ChromaDB
- Retrieval top-k: 4

Only add real client curriculum documents after verifying their source and contents. The included curriculum examples are not a substitute for the complete client curriculum.

## 6. Running the Application

### Advisor Request

```powershell
python -m src.main --student-id DEMO-001 --thread-id demo-session-001 --query "What modules have I completed?"
```

### Assessor Request

```powershell
python -m src.main --student-id DEMO-001 --thread-id demo-session-002 --query "Grade this factorial solution" --code "print(5*4*3*2*1)"
```

Use a unique `thread_id` for each independent conversation.

### Human-in-the-Loop Placement

When a request reaches an eligible Tier-1 placement decision, the graph pauses using LangGraph `interrupt()`.

The workflow can be resumed from Python using the orchestrator's `approve_placement()` method with either:

- `approved`
- `rejected`

Human approval is a workflow decision. It does not establish that a real job vacancy exists or guarantee a placement match.

## 7. Running Tests

Run the complete offline test suite:

```powershell
python -m pytest -q
```

The test suite covers:

- Database tools and read-only query behavior
- Code execution restrictions
- RAG retrieval
- Advisor behavior
- Structured assessment and