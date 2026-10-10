from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import (
    auth_router, resume_router, match_router,
    interview_router, applications_router, chat_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Job Search & Resume Assistant",
    description="Local-LLM-powered resume matching, tailoring, interview prep, and application tracking.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(resume_router.router)
app.include_router(match_router.router)
app.include_router(interview_router.router)
app.include_router(applications_router.router)
app.include_router(chat_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}
