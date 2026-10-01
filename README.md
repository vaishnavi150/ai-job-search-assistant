# AI Job Search & Resume Assistant

A full-stack AI assistant for job searching — resume parsing, semantic
job-match scoring, RAG-grounded resume tailoring, interview question
generation, a live mock interview, and SQL-backed application tracking.
Runs entirely on **free, local/open-source infrastructure** — no OpenAI key,
no paid API, ₹0 to run.

## Tech stack

| Component | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | FastAPI |
| Database | SQLite by default, swappable for PostgreSQL |
| AI | **Ollama** (local LLM - e.g. Llama 3.2) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector DB | FAISS |
| PDF parsing | PyMuPDF |
| DOCX parsing | python-docx |
| Auth | JWT (python-jose + passlib/bcrypt) |
| API testing | Postman collection included |

## Architecture

```
React UI  --(JWT)-->  FastAPI
                          |
        +-----------------+------------------+
        |                 |                  |
  Resume Parser      Job Matcher       AI Services (Ollama)
  (PyMuPDF/docx)   (sentence-transf.)   - bullet tailoring (RAG)
        |                 |             - interview questions
        v                 v             - mock interview chat
   chunk + embed    cosine similarity    - career chat (RAG)
        |
        v
   FAISS index (per user)
        ^
        | retrieval
        +-- used by bullet tailoring & chat for grounding
```

Every AI feature that generates text (tailored bullets, interview
questions, mock interview replies, career chat) calls a **local Ollama
model** — nothing leaves your machine, and there's no API bill. Retrieval
(FAISS + embeddings) grounds the LLM in the user's actual resume so it
can't invent experience they don't have.

## What each feature demonstrates

| Feature | AI/eng concept |
|---|---|
| Resume upload → parsed & chunked | Document processing |
| Chunk embedding → FAISS index | Embeddings, vector databases, semantic search |
| Resume ↔ JD match score | Similarity scoring, NLP |
| Missing skill detection | Keyword extraction |
| Tailored bullets / cover letter | RAG, prompt engineering, LLMs |
| Interview question generation | Prompt engineering, LLMs |
| Mock interview | Multi-turn LLM chat, conversation state |
| Application tracker | SQL, REST APIs |
| Auth | JWT, FastAPI dependencies |
| AI chat assistant | RAG + LLM chat |

## Setup

### 1. Install and start Ollama

Ollama runs the LLM locally - no API key needed.

```bash
# macOS
brew install ollama
# Linux
curl -fsSL https://ollama.com/install.sh | sh
# Windows: download from https://ollama.com/download

ollama serve                # starts the local server on :11434
ollama pull llama3.2        # ~2GB download, one-time
```

Leave `ollama serve` running in its own terminal (on macOS/Windows the
desktop app runs this for you automatically).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # defaults work out of the box with Ollama running
python scripts/init_db.py
uvicorn app.main:app --reload       # http://localhost:8000
```

API docs: http://localhost:8000/docs

**Note on first run:** `sentence-transformers` downloads its embedding
model (~90MB) from Hugging Face the first time you upload a resume. It's
cached locally after that - no internet needed on subsequent runs.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env                # points at http://localhost:8000 by default
npm run dev                         # http://localhost:5173
```

Open http://localhost:5173, register an account, and you're in.

### 4. (Optional) Postman

Import `postman/AI_Job_Assistant.postman_collection.json`, set the
`base_url` and `token` collection variables, and hit endpoints directly.

## Using it

1. **Register / log in** - JWT-based auth, each user's resume and
   applications are private to their account.
2. **Upload a resume** (PDF/DOCX/TXT) on the Resume tab.
3. **Match & Tailor** - paste a job description to get a similarity score,
   missing-skills list, and tailored bullet points grounded in your resume.
4. **Interview Qs** - generate likely questions from a job description.
5. **Mock Interview** - a live chat where the AI asks questions one at a
   time and gives feedback on your answers.
6. **Applications** - track every application's status in SQL.
7. **AI Chat** - general career questions, grounded in your resume when relevant.

## Configuration

Backend `.env` (see `backend/.env.example`):

| Variable | Default | Notes |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2` | Swap for any model you've `ollama pull`ed (e.g. `phi3`, `mistral`) for speed/quality trade-offs |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Change if Ollama runs elsewhere |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Any sentence-transformers model |
| `DATABASE_URL` | `sqlite:///./ai_job_assistant.db` | Swap for a Postgres URL if you want |
| `SECRET_KEY` | dev default | **Change this** if you ever deploy it anywhere real |

## Project layout

```
backend/
  app/
    main.py                FastAPI app + CORS + router registration
    config.py               Settings from .env
    database.py / models.py  SQLAlchemy setup, User/Resume/Application tables
    auth/                     JWT + password hashing, get_current_user dependency
    routers/                  auth, resume, match, interview, applications, chat
    services/
      resume_parser.py         PDF/DOCX/TXT text extraction
      embeddings.py             sentence-transformers wrapper
      vector_store.py           per-user FAISS index (build/search)
      llm.py                     Ollama client (generate/chat)
      matcher.py                 semantic match score + skill gaps
      bullet_improver.py          RAG-grounded bullet tailoring
      interview.py                 question generation + mock interview logic
  scripts/init_db.py          creates tables
  tests/                       pytest suite (auth, parsing, chunking, applications API)
frontend/
  src/
    api.js                     fetch wrapper with JWT handling
    context/AuthContext.jsx     login state
    pages/                       Login, Register, Dashboard
    components/tabs/              one component per feature tab
postman/                       API collection for manual testing
```

## Notes on scope / what's simplified for a starter project

- **One resume per user** - re-uploading replaces the previous one and
  rebuilds their FAISS index. Multi-resume support is a natural extension.
- **Mock interview state is client-side** - the frontend sends the full
  conversation history each turn rather than the backend persisting a
  session. Fine for a demo; a `interview_sessions` table would be the
  production version.
- **Skill-gap detection uses a fixed keyword vocabulary** (`matcher.py`) -
  swap for LLM-based extraction if you want it to generalize beyond tech
  roles.
- **No refresh tokens** - JWTs are long-lived (24h by default) rather than
  implementing refresh/rotation, to keep the auth flow simple to read.
- Natural next steps for a stronger portfolio writeup: an eval harness
  (LLM-as-judge scoring of tailored bullets, like the earlier FastAPI-only
  version of this project used), Postgres in Docker Compose alongside the
  backend, and swapping the keyword-based skill matcher for an
  LLM-extracted skill list.
