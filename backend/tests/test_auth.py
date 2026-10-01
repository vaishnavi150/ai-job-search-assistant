import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hash_and_verify():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_roundtrip():
    token = create_access_token(subject="jane@example.com")
    subject = decode_access_token(token)
    assert subject == "jane@example.com"


def test_jwt_rejects_tampered_token():
    token = create_access_token(subject="jane@example.com")
    tampered = token[:-3] + "xyz"
    assert decode_access_token(tampered) is None
