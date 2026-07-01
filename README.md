# Intelligent Candidate Discovery 

A FastAPI service that ingests job descriptions and candidate profiles, then runs them through a multi-stage AI pipeline (semantic + keyword retrieval, hard filtering, feature extraction, ML ranking, and LLM-generated explanations) to surface and justify the best-matching candidates for a role.

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| Data models / ORM | SQLModel (SQLAlchemy) |
| Database | PostgreSQL (`psycopg2` / `asyncpg`) — SQLite also supported |
| Migrations | Alembic |
| Semantic search | Sentence-Transformers embeddings + Faiss |
| Keyword search | `rank-bm25` / `bm25s` |
| Ranking model | LightGBM, scikit-learn |
| LLM (explanations, embeddings) | Google Gemini (`google-genai`, `langchain-google-genai`), Anthropic SDK also available |
| File ingestion | `openpyxl`, `python-docx`, `python-multipart` |
| Dependency management | [uv](https://github.com/astral-sh/uv) |

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py             # Shared FastAPI dependencies (DB session, etc.)
│   │   └── routes/
│   │       ├── jobs.py         # Job CRUD endpoints
│   │       ├── candidates.py   # Candidate CRUD + bulk upload endpoints
│   │       └── pipeline.py     # Pipeline run + results endpoints
│   ├── db/
│   │   ├── models.py           # SQLModel ORM tables (Jobs, Candidates, PipelineRun, RankedResult)
│   │   └── session.py          # Engine/session setup, table creation
│   ├── engine/                 # Core matching pipeline
│   │   ├── retrieval.py        # Semantic (Faiss) + keyword (BM25) retrieval, fused via RRF
│   │   ├── filters.py          # Hard constraint filtering (skills, experience, etc.)
│   │   ├── features.py         # Feature engineering for ranking
│   │   ├── ranker.py           # LightGBM-based candidate scoring
│   │   ├── rerank_explain.py   # LLM re-ranking + human-readable explanations
│   │   └── pipeline.py         # Orchestrates the full pipeline end-to-end
│   ├── models/                 # Pydantic request/response schemas
│   │   ├── job.py               # JobCreate / JobRead
│   │   ├── candidate.py         # CandidateCreate / CandidateRead
│   │   └── result.py            # RankedCandidateResult / PipelineRunRead
│   ├── services/
│   │   ├── embeddings.py       # Embedding generation service
│   │   └── llm.py               # LLM client wrapper (Gemini)
│   ├── config.py               # Settings loaded from environment / .env
│   └── main.py                  # FastAPI app instance, routers, CORS, health check
├── pyproject.toml
├── uv.lock
└── README.md
```

## Discovery Pipeline (`app/engine`)

Given a job and a pool of candidates, the pipeline runs in five stages:

1. **Retrieval** (`retrieval.py`) — Combines semantic search (Faiss + embeddings) with keyword search (BM25), fused with Reciprocal Rank Fusion, to pull the top `RETRIEVAL_TOP_K` candidates.
2. **Filtering** (`filters.py`) — Applies hard constraints (minimum experience, required skills/certs, etc.) to eliminate non-matches.
3. **Feature Extraction** (`features.py`) — Computes signals such as semantic similarity, skill overlap, experience fit, and activity/recency.
4. **Ranking** (`ranker.py`) — Scores and orders candidates using a trained LightGBM model.
5. **Reranking & Explanation** (`rerank_explain.py`) — Sends the top `EXPLANATION_TOP_K` candidates to an LLM (Gemini) to generate a match justification and highlight skill gaps.

The whole flow is orchestrated in `pipeline.py`, and each run is persisted as a `PipelineRun` with its `RankedResult` rows.

## Data Model

| Table | Purpose |
|---|---|
| `jobs` | Job postings — title, description, required skills/certs, minimum experience |
| `candidates` | Candidate profiles — free-text profile, parsed skills/certs, years of experience, profile completeness, last-active date |
| `pipeline_runs` | One row per pipeline execution, tracking status (`pending` / `running` / `completed` / `failed`) |
| `ranked_results` | Per-candidate output of a run — rank, final score, feature breakdown, matched skills, gaps, and justification |

## API Overview

Base URL: `http://localhost:8000`

### Jobs — `/jobs`
| Method | Path | Description |
|---|---|---|
| `GET` | `/jobs` | List all jobs |
| `POST` | `/jobs` | Create a job |
| `GET` | `/jobs/{job_id}` | Get a single job |

### Candidates — `/candidates`
| Method | Path | Description |
|---|---|---|
| `GET` | `/candidates` | List all candidates |
| `POST` | `/candidates/upload` | Bulk-upload candidates from a file (e.g. spreadsheet) |
| `GET` | `/candidates/{candidate_id}` | Get a single candidate |

### Pipeline — `/pipeline`
| Method | Path | Description |
|---|---|---|
| `POST` | `/pipeline/run` | Trigger a pipeline run for a job against the candidate pool |
| `GET` | `/pipeline/{run_id}` | Get the status and ranked results of a run |

### Health
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Basic liveness check — returns `{"status": "ok"}` |

Full interactive documentation is auto-generated by FastAPI once the server is running:
- Swagger UI — `http://localhost:8000/docs`
- ReDoc — `http://localhost:8000/redoc`

## Setup & Installation

1. **Install `uv`** (if not already installed) — see the [uv installation guide](https://github.com/astral-sh/uv#installation).

2. **Install dependencies** from the `backend` directory:
   ```bash
   uv sync
   ```
   (or `pip install -e .` if you prefer plain pip/venv)

3. **Configure environment variables.** Create a `.env` file in `backend/` with at least:
   ```env
   # App
   APP_NAME=Intelligent Candidate Discovery
   DEBUG=true

   # Database
   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/candidates
   # or, for local/dev without Postgres:
   # DATABASE_URL=sqlite:///./test.db

   # Gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_EMBEDDING_MODEL=gemini-embedding-2-preview

   # Pipeline tuning
   RETRIEVAL_TOP_K=200
   EXPLANATION_TOP_K=50
   BM25_WEIGHT=0.4
   EMBEDDING_WEIGHT=0.6
   ```
   See `app/config.py` for the full list of settings and their defaults.

   > **Note:** the current `db/session.py` engine is configured with `sslmode=require`, which targets a managed Postgres instance (e.g. Neon/Supabase). If you point `DATABASE_URL` at local Postgres without SSL, or at SQLite, remove/adjust that `connect_args`.

## Running the Server

```bash
uv run uvicorn app.main:app --reload
```

or, with the virtual environment activated manually:

```bash
uvicorn app.main:app --reload
```

Database tables are created automatically on startup via the app's lifespan hook — no separate migration step is required for a fresh SQLite/Postgres database (Alembic is available for schema evolution beyond that).

The API will be available at `http://localhost:8000`, with CORS enabled for `http://localhost:3000` and `http://localhost:5173` (typical local frontend dev servers).

## Development Tools

- **Linting/formatting:** `ruff`
  ```bash
  uv run ruff check .
  uv run ruff format .
  ```
- **Testing:** `pytest` + `pytest-asyncio`
  ```bash
  uv run pytest
  ```

## Typical Workflow

1. `POST /jobs` — create a job with its required skills, min experience, and certs.
2. `POST /candidates/upload` (or `POST /candidates` per-record) — load the candidate pool.
3. `POST /pipeline/run` — kick off a discovery run for that job.
4. `GET /pipeline/{run_id}` — poll for status and retrieve ranked, explained results once `completed`.
