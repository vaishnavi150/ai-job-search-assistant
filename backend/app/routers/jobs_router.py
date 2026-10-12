import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.models import User
from app.schemas import JobSearchResponse
from app.services import job_search, vector_store
from app.services.embeddings import EmbeddingModelUnavailableError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/search", response_model=JobSearchResponse)
def search(
    q: str = Query(min_length=2, max_length=100, description="Keywords, e.g. 'python backend'"),
    location: str = Query(default="", max_length=60),
    remote_only: bool = False,
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    try:
        resume_vectors = vector_store.chunk_vectors(current_user.id)
    except EmbeddingModelUnavailableError:
        resume_vectors = None  # still return keyword results, just unranked

    try:
        result = job_search.search_jobs(q, location, remote_only, resume_vectors, limit)
    except EmbeddingModelUnavailableError:
        result = job_search.search_jobs(q, location, remote_only, None, limit)

    if not result["sources"]:
        raise HTTPException(
            status_code=503,
            detail="Job listing services are unreachable right now. Please try again in a few minutes.",
        )
    return result
