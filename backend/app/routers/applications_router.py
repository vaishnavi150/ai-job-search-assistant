from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Application
from app.schemas import ApplicationCreate, ApplicationUpdate, ApplicationOut
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])

VALID_STATUSES = {"saved", "applied", "interviewing", "offer", "rejected"}


@router.get("", response_model=list[ApplicationOut])
def list_applications(status: str | None = None, current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    query = db.query(Application).filter(Application.user_id == current_user.id)
    if status:
        query = query.filter(Application.status == status)
    return query.order_by(Application.updated_at.desc()).all()


@router.post("", response_model=ApplicationOut)
def create_application(payload: ApplicationCreate, current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    data = payload.model_dump()
    if data["status"] not in VALID_STATUSES:
        data["status"] = "saved"
    app_row = Application(user_id=current_user.id, **data)
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    return app_row


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(application_id: int, payload: ApplicationUpdate,
                        current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    app_row = db.query(Application).filter(
        Application.id == application_id, Application.user_id == current_user.id
    ).first()
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(app_row, key, value)
    db.commit()
    db.refresh(app_row)
    return app_row


@router.delete("/{application_id}", status_code=204)
def delete_application(application_id: int, current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    app_row = db.query(Application).filter(
        Application.id == application_id, Application.user_id == current_user.id
    ).first()
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app_row)
    db.commit()
