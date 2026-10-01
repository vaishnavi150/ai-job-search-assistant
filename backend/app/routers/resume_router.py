from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Resume
from app.schemas import ResumeOut
from app.auth.dependencies import get_current_user
from app.services.resume_parser import extract_text
from app.utils.chunking import chunk_text
from app.services import vector_store
from app.services.embeddings import EmbeddingModelUnavailableError

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    try:
        text = extract_text(file_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not text.strip():
        raise HTTPException(status_code=400, detail="Couldn't extract any text from that file.")

    existing = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if existing:
        existing.filename = file.filename
        existing.raw_text = text
    else:
        existing = Resume(user_id=current_user.id, filename=file.filename, raw_text=text)
        db.add(existing)
    db.commit()
    db.refresh(existing)

    # Rebuild the FAISS index for this user so tailoring/chat retrieval is current.
    chunks = chunk_text(text)
    try:
        vector_store.build_index(current_user.id, chunks)
    except EmbeddingModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return existing


@router.get("/me", response_model=ResumeOut)
def get_my_resume(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")
    return resume
