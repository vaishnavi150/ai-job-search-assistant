import logging
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User, Resume
from app.schemas import ResumeOut
from app.auth.dependencies import get_current_user
from app.services.resume_parser import extract_text
from app.utils.chunking import chunk_text
from app.services import vector_store
from app.services.embeddings import EmbeddingModelUnavailableError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume", tags=["resume"])

MAX_RESUME_CHARS = 60_000


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    max_bytes = settings.max_upload_mb * 1024 * 1024
    # Read one byte past the limit so oversized files are rejected without
    # buffering the whole thing.
    file_bytes = await file.read(max_bytes + 1)
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File is too large. The limit is {settings.max_upload_mb} MB.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="That file is empty.")

    filename = os.path.basename(file.filename or "resume")[:200]
    try:
        text = extract_text(file_bytes, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if len(text) < 50:
        raise HTTPException(
            status_code=400,
            detail="We couldn't find enough text in that file. If it's a scanned PDF, "
                   "export a text-based PDF or DOCX instead.",
        )
    text = text[:MAX_RESUME_CHARS]

    # Embed first, so a failure doesn't leave the database and index out of sync.
    try:
        vector_store.build_index(current_user.id, chunk_text(text))
    except EmbeddingModelUnavailableError as exc:
        logger.error("Embedding model unavailable during upload: %s", exc)
        raise HTTPException(status_code=503, detail="Resume analysis is temporarily unavailable. Please try again shortly.")

    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if resume:
        resume.filename = filename
        resume.raw_text = text
    else:
        resume = Resume(user_id=current_user.id, filename=filename, raw_text=text)
        db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/me", response_model=ResumeOut)
def get_my_resume(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    return resume


@router.delete("/me", status_code=204)
def delete_my_resume(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    db.delete(resume)
    db.commit()
    vector_store.delete_index(current_user.id)
