import datetime as dt
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import (
    burn_verification_time, create_access_token, hash_password, hash_reset_token,
    needs_rehash, new_reset_token, verify_password,
)
from app.config import settings
from app.database import get_db
from app.models import PasswordResetToken, User, utcnow
from app.schemas import (
    ChangePasswordRequest, ForgotPasswordRequest, MessageResponse, ResetPasswordRequest,
    ResetTokenCheck, Token, UserCreate, UserOut,
)
from app.services.email import send_password_reset_email
from app.utils import rate_limit as rl

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

FORGOT_PASSWORD_MESSAGE = (
    "If an account exists for that email, we've sent a link to reset your password. "
    "It expires in {minutes} minutes."
)
INVALID_RESET_LINK = "This reset link is invalid or has expired. Please request a new one."


def _find_user(db: Session, email: str) -> User | None:
    # Case-insensitive so accounts created before emails were normalized still match.
    return db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()


def _issue_token(user: User) -> Token:
    return Token(
        access_token=create_access_token(subject=user.email, token_version=user.token_version or 0),
        expires_in=settings.access_token_expire_minutes * 60,
    )


def _set_password(user: User, new_password: str) -> None:
    """Changing the password also revokes every existing session."""
    user.hashed_password = hash_password(new_password)
    user.token_version = (user.token_version or 0) + 1
    user.password_changed_at = utcnow()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    ip_key = rl.client_ip(request)
    rl.enforce(rl.register_by_ip, ip_key, "Too many sign-ups from this network.")
    rl.register_by_ip.hit(ip_key)

    if _find_user(db, payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists. Try logging in.")
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two simultaneous sign-ups with the same email
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists. Try logging in.")
    db.refresh(user)
    logger.info("User registered id=%s", user.id)
    return user


@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm uses `username` - we treat it as the email.
    email = form_data.username.strip().lower()
    ip_key = rl.client_ip(request)
    rl.enforce(rl.login_attempts_by_ip, ip_key, "Too many login attempts.")
    rl.enforce(rl.login_failures_by_email, email, "Too many failed login attempts for this account.")
    rl.login_attempts_by_ip.hit(ip_key)

    user = _find_user(db, email) if len(form_data.password) <= 128 else None
    if user is None:
        burn_verification_time()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        rl.login_failures_by_email.hit(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    rl.login_failures_by_email.reset(email)
    if needs_rehash(user.hashed_password):
        # Transparently upgrade legacy bcrypt hashes to Argon2id.
        user.hashed_password = hash_password(form_data.password)
        db.commit()
    return _issue_token(user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes every token issued so far, on every device."""
    current_user.token_version = (current_user.token_version or 0) + 1
    db.commit()
    return MessageResponse(message="You've been signed out on all devices.")


@router.post("/change-password", response_model=Token)
def change_password(payload: ChangePasswordRequest, current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    key = str(current_user.id)
    rl.enforce(rl.password_change_by_user, key, "Too many attempts.")
    if not verify_password(payload.current_password, current_user.hashed_password):
        rl.password_change_by_user.hit(key)
        raise HTTPException(status_code=400, detail="Your current password is incorrect.")
    _set_password(current_user, payload.new_password)
    db.commit()
    db.refresh(current_user)
    logger.info("Password changed for user id=%s", current_user.id)
    # Other sessions are now revoked; hand this one a fresh token.
    return _issue_token(current_user)


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
def forgot_password(payload: ForgotPasswordRequest, request: Request, background_tasks: BackgroundTasks,
                    db: Session = Depends(get_db)):
    message = MessageResponse(message=FORGOT_PASSWORD_MESSAGE.format(minutes=settings.password_reset_token_minutes))
    ip_key = rl.client_ip(request)
    rl.enforce(rl.reset_requests_by_ip, ip_key, "Too many reset requests.")
    rl.reset_requests_by_ip.hit(ip_key)

    # Over the per-email limit we silently skip sending, so the response
    # stays identical and can't be used to probe or spam an address.
    if rl.reset_requests_by_email.retry_after(payload.email):
        return message
    rl.reset_requests_by_email.hit(payload.email)

    user = _find_user(db, payload.email)
    if user is None:
        return message

    now = utcnow()
    # One live link at a time: requesting a new one kills older ones.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    token, token_hash = new_reset_token()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + dt.timedelta(minutes=settings.password_reset_token_minutes),
    ))
    db.commit()

    reset_url = f"{settings.public_frontend_url}/reset-password?{urlencode({'token': token})}"
    # Sent after the response so timing doesn't reveal whether the account exists.
    background_tasks.add_task(send_password_reset_email, user.email, reset_url)
    return message


def _get_valid_reset_token(db: Session, token: str) -> PasswordResetToken | None:
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == hash_reset_token(token)).first()
    if row is None or row.used_at is not None or row.expires_at <= utcnow():
        return None
    return row


@router.post("/reset-password/validate", response_model=MessageResponse)
def validate_reset_token(payload: ResetTokenCheck, request: Request, db: Session = Depends(get_db)):
    """Lets the reset page say "link expired" before the user types a password."""
    ip_key = rl.client_ip(request)
    rl.enforce(rl.reset_attempts_by_ip, ip_key, "Too many attempts.")
    if _get_valid_reset_token(db, payload.token) is None:
        rl.reset_attempts_by_ip.hit(ip_key)
        raise HTTPException(status_code=400, detail=INVALID_RESET_LINK)
    return MessageResponse(message="Link is valid.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    ip_key = rl.client_ip(request)
    rl.enforce(rl.reset_attempts_by_ip, ip_key, "Too many attempts.")
    row = _get_valid_reset_token(db, payload.token)
    if row is None:
        rl.reset_attempts_by_ip.hit(ip_key)
        raise HTTPException(status_code=400, detail=INVALID_RESET_LINK)

    user = row.user
    now = utcnow()
    # Claim the token atomically: if two requests race with the same link,
    # only the one whose UPDATE flips used_at gets to change the password.
    claimed = db.query(PasswordResetToken).filter(
        PasswordResetToken.id == row.id, PasswordResetToken.used_at.is_(None)
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    if claimed != 1:
        db.rollback()
        raise HTTPException(status_code=400, detail=INVALID_RESET_LINK)
    _set_password(user, payload.password)
    # Burn any other outstanding links for the account.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
    ).update({PasswordResetToken.used_at: now}, synchronize_session=False)
    db.commit()
    rl.login_failures_by_email.reset(user.email.lower())
    logger.info("Password reset completed for user id=%s", user.id)
    return MessageResponse(message="Your password has been reset. You can now log in with your new password.")
