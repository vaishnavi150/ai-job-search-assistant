import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.migrations import run_migrations
from app.routers import (
    auth_router, resume_router, match_router, jobs_router,
    interview_router, applications_router, chat_router,
)

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    if not settings.email_enabled:
        logger.warning("Email isn't configured - password reset emails won't be sent.")
    logger.info("Started (LLM provider: %s)", settings.llm_provider)
    yield


app = FastAPI(
    title="Nextrung API",
    description="Job search, resume matching, tailoring, interview prep, and application tracking.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    # Auth uses a bearer token, not cookies, so credentials aren't needed.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if settings.is_production:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if request.url.path.startswith("/auth"):
        response.headers["Cache-Control"] = "no-store"
    return response


def _readable(error: dict) -> str:
    field = ".".join(str(p) for p in error.get("loc", [])[1:]) or "request"
    msg = error.get("msg", "is invalid")
    if msg.startswith("Value error, "):
        return msg.removeprefix("Value error, ")
    labels = {
        "job_description": "Job description", "email": "Email", "password": "Password",
        "message": "Message", "company": "Company", "job_title": "Job title", "q": "Search",
    }
    label = labels.get(field.split(".")[0], field.replace("_", " ").capitalize())
    if label == "Email" and error.get("type") == "value_error":
        return "Enter a valid email address."
    if error.get("type") == "string_too_short":
        min_len = error.get("ctx", {}).get("min_length")
        return f"{label} is too short" + (f" (at least {min_len} characters)." if min_len and min_len > 1 else ".")
    if error.get("type") == "string_too_long":
        return f"{label} is too long (max {error.get('ctx', {}).get('max_length')} characters)."
    if error.get("type") == "missing":
        return f"{label} is required."
    return f"{label}: {msg}."


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    # A single readable string is easier for the UI than Pydantic's error list.
    messages = list(dict.fromkeys(_readable(e) for e in exc.errors()))
    return JSONResponse(status_code=422, content={"detail": " ".join(messages[:3])})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side. Please try again."})


app.include_router(auth_router.router)
app.include_router(resume_router.router)
app.include_router(match_router.router)
app.include_router(jobs_router.router)
app.include_router(interview_router.router)
app.include_router(applications_router.router)
app.include_router(chat_router.router)


@app.get("/health")
def health():
    """Liveness + database check, used by Render's health checks."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: database unreachable")
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return {"status": "ok"}


@app.get("/config")
def public_config():
    """Non-secret feature flags so the UI can explain what's available."""
    return {
        "email_enabled": settings.email_enabled,
        "llm_provider": settings.llm_provider,
        "max_upload_mb": settings.max_upload_mb,
    }
