from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Resume
from app.schemas import MatchRequest, MatchResponse, BulletRequest, BulletResponse
from app.auth.dependencies import get_current_user
from app.services.matcher import match_resume
from app.services.bullet_improver import improve_bullets
from app.services.llm import OllamaUnavailableError
from app.services.embeddings import EmbeddingModelUnavailableError

router = APIRouter(prefix="/match", tags=["match"])


@router.post("", response_model=MatchResponse)
def match(payload: MatchRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    try:
        return match_resume(resume.raw_text, payload.job_description)
    except EmbeddingModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/bullets", response_model=BulletResponse)
def bullets(payload: BulletRequest, current_user: User = Depends(get_current_user)):
    try:
        result = improve_bullets(current_user.id, payload.job_description)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except EmbeddingModelUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not result["bullets"] and result.get("note"):
        raise HTTPException(status_code=400, detail=result["note"])
    return result
