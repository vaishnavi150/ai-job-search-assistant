import datetime as dt
import hashlib
import secrets

import bcrypt
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings

# Argon2id with the library's RFC 9106 "low memory" defaults - sized for
# small hosts like Render's free tier.
_hasher = PasswordHasher()

# Constant-time decoy so login takes the same time whether or not the email
# exists (prevents account enumeration by timing).
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies Argon2id hashes, plus legacy bcrypt hashes from v0.1.0."""
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(plain_password.encode()[:72], hashed_password.encode())
        except ValueError:
            return False
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    if not hashed_password.startswith("$argon2"):
        return True
    try:
        return _hasher.check_needs_rehash(hashed_password)
    except InvalidHashError:
        return True


def burn_verification_time() -> None:
    verify_password("not-the-password", _DUMMY_HASH)


def create_access_token(subject: str, token_version: int = 0) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": subject,
        "tv": token_version,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    """Returns the verified claims, or None for any invalid/expired token."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError:
        return None
    return payload


def new_reset_token() -> tuple[str, str]:
    """Returns (token for the email link, hash to store)."""
    token = secrets.token_urlsafe(32)
    return token, hash_reset_token(token)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
