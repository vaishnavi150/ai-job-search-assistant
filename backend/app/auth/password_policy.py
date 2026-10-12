"""Password strength rules, shared by registration, reset, and change-password.
The frontend mirrors these rules (src/utils/password.js) for instant
feedback, but this is the copy that's enforced."""
import re

MIN_LENGTH = 8
MAX_LENGTH = 128

# A short list of passwords that technically pass the character rules but
# appear at the top of every breach list.
_COMMON = {
    "password1!", "password123!", "p@ssw0rd", "p@ssw0rd1", "p@ssword1", "passw0rd!",
    "qwerty123!", "welcome1!", "welcome123!", "admin123!", "letmein1!", "iloveyou1!",
    "abc123!@#", "changeme1!", "test1234!", "password@123", "india@123", "qwerty@123",
}


def password_problems(password: str, email: str | None = None) -> list[str]:
    """Returns human-readable reasons the password is rejected ([] if OK)."""
    problems = []
    if len(password) < MIN_LENGTH:
        problems.append(f"at least {MIN_LENGTH} characters")
    if len(password) > MAX_LENGTH:
        problems.append(f"at most {MAX_LENGTH} characters")
    if not re.search(r"[a-z]", password):
        problems.append("a lowercase letter")
    if not re.search(r"[A-Z]", password):
        problems.append("an uppercase letter")
    if not re.search(r"\d", password):
        problems.append("a number")
    if not re.search(r"[^A-Za-z0-9]", password):
        problems.append("a special character")
    if problems:
        return problems

    lowered = password.lower()
    if lowered in _COMMON:
        return ["to not be a commonly used password"]
    if email:
        local = email.split("@", 1)[0].lower()
        if len(local) >= 4 and local in lowered:
            return ["to not contain your email address"]
    return []


def validate_password(password: str, email: str | None = None) -> None:
    problems = password_problems(password, email)
    if problems:
        raise ValueError("Password must have " + ", ".join(problems) + ".")
