import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.auth.security import (
    hash_password, verify_password, needs_rehash, create_access_token, decode_access_token,
    new_reset_token, hash_reset_token,
)
from app.auth.password_policy import password_problems


def test_password_hash_and_verify():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_jwt_roundtrip():
    token = create_access_token(subject="jane@example.com", token_version=3)
    claims = decode_access_token(token)
    assert claims["sub"] == "jane@example.com"
    assert claims["tv"] == 3


def test_jwt_rejects_tampered_token():
    token = create_access_token(subject="jane@example.com")
    tampered = token[:-3] + "xyz"
    assert decode_access_token(tampered) is None


def test_hash_is_argon2id_and_not_rehashed():
    hashed = hash_password("Str0ng!Passw0rd")
    assert hashed.startswith("$argon2id$")
    assert not needs_rehash(hashed)


def test_reset_tokens_are_random_and_hashed():
    token_a, hash_a = new_reset_token()
    token_b, _ = new_reset_token()
    assert token_a != token_b and len(token_a) >= 40
    assert hash_a == hash_reset_token(token_a) != token_a


def test_password_policy_accepts_strong_password():
    assert password_problems("Str0ng!Passw0rd") == []
    assert password_problems("short") != []
