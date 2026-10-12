# AI Job Search & Resume Assistant

A full-stack AI assistant for the job hunt: live job search ranked against
your resume, resume ↔ job-description match scoring with skill gaps,
RAG-grounded resume tailoring, interview question generation, a live mock
interviewer, a career chat assistant, and an application tracker.

Runs on **free infrastructure**: a local Ollama model or Groq's free tier
for text generation, open-source embeddings, free public job boards, and
Render's free tier for hosting. No paid API is required.

## Features

| Feature | How it works |
|---|---|
| Accounts | Register / log in / log out, change password, "sign out of all devices" |
| Forgot password | Emailed, single-use, 30-minute reset links (Brevo HTTP API or SMTP) |
| Resume upload | PDF / DOCX / TXT parsed, chunked, embedded into a per-user FAISS index |
| Find jobs | Live listings from Remotive + Arbeitnow, re-ranked by similarity to your resume |
| Match & tailor | Semantic match score + skill coverage, missing skills, tailored bullets grounded in your resume |
| Interview questions | Role-specific technical and behavioural questions |
| Mock interview | Multi-turn AI interviewer with feedback after each answer |
| Applications | Track jobs from saved → applied → interviewing → offer / rejected, with notes and links |
| Career chat | General career Q&A, grounded in your resume when relevant |

When an AI service is unavailable the API returns a clear error (HTTP 503)
instead of made-up output, and job search reports which boards were
unreachable.

## Tech stack

| Component | Technology |
|---|---|
| Frontend | React 18 + Vite + React Router |
| Backend | FastAPI, SQLAlchemy 2 |
| Database | SQLite locally, PostgreSQL on Render |
| LLM | Ollama (local) or Groq (hosted, OpenAI-compatible) |
| Embeddings | fastembed (ONNX) running `all-MiniLM-L6-v2` |
| Vector search | FAISS |
| Parsing | PyMuPDF, python-docx |
| Auth | Argon2id password hashing, PyJWT bearer tokens with revocation |
| Tests | pytest (backend), Vitest (frontend) |

## Security

- Passwords hashed with **Argon2id**; legacy bcrypt hashes from v0.1 are
  verified and upgraded on next login.
- Password policy (enforced on the server, mirrored in the UI): 8–128
  characters, upper- and lowercase letters, a number, a special character;
  common breached passwords and passwords containing your email are rejected.
- Login is rate-limited per account and per IP; registration, reset
  requests and reset attempts are rate-limited too. Login takes the same
  time whether or not the email exists.
- Reset tokens come from `secrets.token_urlsafe(32)`, are stored only as
  SHA-256 hashes, expire after `PASSWORD_RESET_TOKEN_MINUTES`, work once
  (claimed atomically), and requesting a new one invalidates older ones.
  The forgot-password response is identical whether or not the account
  exists.
- Changing or resetting a password revokes every existing session.
- Strict CORS allow-list, security headers on the API and static site
  (CSP, `X-Frame-Options`, `nosniff`, HSTS in production), no stack traces
  in API responses, no secrets or reset links in logs.
- The app refuses to start in production with the default `SECRET_KEY`.

## Local development

Requires Python 3.11+ (Render uses 3.12) and Node 18+.

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env                # then edit - see "Configuration"
uvicorn app.main:app --reload       # http://localhost:8000  (docs at /docs)
```

Tables and column migrations run automatically at startup
(`python scripts/init_db.py` does the same by hand). The embedding model
(~90 MB) downloads on first use and is cached in `.fastembed_cache/`.

For text generation, either:

- **Ollama (local, no key):** install from https://ollama.com, then
  `ollama pull llama3.2` and keep `ollama serve` running; set `LLM_PROVIDER=ollama`.
- **Groq (hosted, free tier):** get a key at https://console.groq.com/keys;
  set `LLM_PROVIDER=groq` and `GROQ_API_KEY=...`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env                # VITE_API_BASE_URL=http://localhost:8000
npm run dev                         # http://localhost:5173
```

### 3. Tests

```bash
cd backend  && pytest               # API, auth, reset flow, parsing, matching, job search
cd frontend && npm test             # password rules + API client
cd frontend && npm run build        # production build
```

The backend tests fake the LLM, embeddings and job boards, so they run
offline and never touch your real database.

## Configuration

Backend variables (`backend/.env` locally, the service's **Environment**
tab on Render). Never commit real values - `.env` files are git-ignored.

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | **Yes in production** | Long random string: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `DATABASE_URL` | Production | Postgres URL; defaults to local SQLite |
| `FRONTEND_ORIGIN` | **Yes** | Comma-separated allowed origins, e.g. `https://ai-job-assistant-web.onrender.com` |
| `FRONTEND_URL` | No | Base URL for reset links; defaults to the first `FRONTEND_ORIGIN` |
| `LLM_PROVIDER` | Yes | `groq` or `ollama` |
| `GROQ_API_KEY` | With Groq | From console.groq.com |
| `GROQ_MODEL` | No | Default `openai/gpt-oss-120b` |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | With Ollama | Defaults `http://localhost:11434` / `llama3.2` |
| `EMAIL_PROVIDER` | For password reset | `brevo`, `smtp`, or empty to disable |
| `EMAIL_FROM` | For password reset | Sender address (must be verified in Brevo) |
| `EMAIL_FROM_NAME` | No | Default `AI Job Search Assistant` |
| `BREVO_API_KEY` | With Brevo | Brevo → SMTP & API → API keys |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `SMTP_USE_TLS` | With SMTP | e.g. Gmail: `smtp.gmail.com`, `587`, your address, an **App Password** |
| `PASSWORD_RESET_TOKEN_MINUTES` | No | Default 30 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default 480 (8 h) |
| `MAX_UPLOAD_MB` | No | Default 5 |
| `JOB_CACHE_MINUTES` | No | How long job-board feeds are cached; default 360 |

Frontend (`frontend/.env`, or the static site's Environment tab - baked in
at build time, so redeploy after changing it):

| Variable | Notes |
|---|---|
| `VITE_API_BASE_URL` | Backend URL, no trailing slash, e.g. `https://ai-job-assistant-api.onrender.com` |

### Setting up password-reset email

Render's free tier blocks outbound SMTP ports, so on Render use **Brevo**
(free, 300 emails/day, sent over HTTPS):

1. Create a free account at https://www.brevo.com.
2. *Senders, Domains & Dedicated IPs → Senders*: add and verify the address
   you'll send from.
3. *SMTP & API → API Keys*: create a key.
4. On the Render API service set `EMAIL_PROVIDER=brevo`,
   `BREVO_API_KEY=<key>`, `EMAIL_FROM=<verified address>`.

After a reset request the API log shows either `Password reset email sent`
or `Password reset email failed: Brevo returned …` with Brevo's reason.
The usual ones: `Key not found` (wrong key — use an API key starting `xkeysib-`, not
the SMTP key), `unrecognised IP address` (turn off *Security → Authorised IPs*
in Brevo, since Render's outgoing IP changes), or an unverified sender.

For local development you can instead use any SMTP server (Gmail with an
App Password, Mailtrap, …) with `EMAIL_PROVIDER=smtp`. If email isn't
configured the app still works; the Forgot Password page says reset emails
aren't available and the server logs a warning.

## Deploying to Render

`render.yaml` is a Render Blueprint defining the Postgres database
(`ai-job-assistant-db`), the API (`ai-job-assistant-api`, Python, root
`backend/`) and the static frontend (`ai-job-assistant-web`, root
`frontend/`).

- **API** - build: `pip install -r requirements.txt && python -m app.services.embeddings`
  (pre-downloads the embedding model); start:
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`; health check `/health`;
  Python `3.12.10`.
- **Web** - build: `npm ci && npm run build`; publish `dist`; all routes
  rewrite to `/index.html` so deep links like `/reset-password` work.

With auto-deploy on, pushing to the connected branch redeploys both
services. After the first deploy of this version, set the new variables on
the API service (`EMAIL_PROVIDER`, `BREVO_API_KEY`, `EMAIL_FROM`) and make
sure `FRONTEND_ORIGIN` on the API matches the static site URL and
`VITE_API_BASE_URL` on the static site matches the API URL.

Free-tier notes: the API sleeps after ~15 minutes idle (the UI shows a
"waking up" banner on slow first requests), the disk is ephemeral (FAISS
indexes are rebuilt automatically from resumes stored in Postgres), and
rate-limit counters are in memory (fine for the single free instance).

## Project layout

```
backend/
  app/
    main.py               App, CORS, security headers, error handlers, /health, /config
    config.py              Settings from environment
    database.py / models.py / migrations.py
    auth/                  Argon2id hashing, JWT, password policy, current-user dependency
    routers/               auth, resume, jobs, match, interview, applications, chat
    services/              resume_parser, embeddings, vector_store, llm, matcher,
                           bullet_improver, interview, job_search, email
    utils/                 chunking, rate_limit
  scripts/init_db.py
  tests/
frontend/
  src/
    api.js                 fetch wrapper: auth header, timeouts, friendly errors
    context/AuthContext.jsx
    components/            AppLayout (sidebar), AuthLayout, ui kit, PasswordField, ChatWindow…
    pages/                 Login, Register, ForgotPassword, ResetPassword, Overview, Resume,
                           Jobs, Match, Interview, MockInterview, Applications, Chat, Account
    utils/password.js      client-side mirror of the password policy
postman/                   API collection for manual testing
render.yaml                Render Blueprint
```

## Known limitations

- One resume per user; re-uploading replaces it.
- Mock-interview and chat history live in the browser tab, not the database.
- Skill-gap detection uses a curated keyword vocabulary (`matcher.py`), so
  it's strongest for tech roles.
- Job search covers Remotive (remote jobs) and Arbeitnow (mostly Europe);
  coverage for other regions is limited.
- Sessions are 8-hour bearer tokens stored in `localStorage` (no refresh
  tokens); password changes and "sign out everywhere" revoke them server-side.
