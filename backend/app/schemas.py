import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.auth.password_policy import validate_password

# Generous for a real job posting, small enough to bound LLM cost and latency.
JobDescription = Field(min_length=30, max_length=20_000)
ApplicationStatus = Literal["saved", "applied", "interviewing", "offer", "rejected"]


def _strip_value(value):
    return value.strip() if isinstance(value, str) else value


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)
    confirm_password: Optional[str] = Field(default=None, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def check_password(self):
        if self.confirm_password is not None and self.confirm_password != self.password:
            raise ValueError("Passwords don't match.")
        validate_password(self.password, self.email)
        return self


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: Optional[dt.datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class ResetTokenCheck(BaseModel):
    token: str = Field(max_length=200)


class ResetPasswordRequest(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(max_length=128)
    confirm_password: str = Field(max_length=128)

    @model_validator(mode="after")
    def check_password(self):
        if self.confirm_password != self.password:
            raise ValueError("Passwords don't match.")
        validate_password(self.password)
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(max_length=128)
    confirm_password: str = Field(max_length=128)

    @model_validator(mode="after")
    def check_password(self):
        if self.confirm_password != self.new_password:
            raise ValueError("Passwords don't match.")
        if self.new_password == self.current_password:
            raise ValueError("New password must be different from your current password.")
        validate_password(self.new_password)
        return self


class MessageResponse(BaseModel):
    message: str


# --- Resume ---
class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    raw_text: str
    created_at: Optional[dt.datetime] = None


# --- Matching ---
class MatchRequest(BaseModel):
    job_description: str = JobDescription
    strip_text = field_validator("job_description", mode="before")(_strip_value)


class MatchResponse(BaseModel):
    match_score: float
    semantic_score: float
    skill_coverage: Optional[float] = None
    matched_skills: list[str]
    missing_skills: list[str]
    summary: str


class BulletRequest(BaseModel):
    job_description: str = JobDescription
    strip_text = field_validator("job_description", mode="before")(_strip_value)


class BulletResponse(BaseModel):
    bullets: list[str]
    grounded_on: list[str]


# --- Interview ---
class InterviewQuestionsRequest(BaseModel):
    job_description: str = JobDescription
    num_questions: int = Field(default=5, ge=3, le=15)
    strip_text = field_validator("job_description", mode="before")(_strip_value)


class InterviewQuestionsResponse(BaseModel):
    questions: list[str]


class ChatTurn(BaseModel):
    # "system" is deliberately not allowed: the server owns the system prompt.
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12_000)


class MockInterviewRequest(BaseModel):
    job_description: str = JobDescription
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)
    strip_text = field_validator("job_description", mode="before")(_strip_value)


class MockInterviewResponse(BaseModel):
    reply: str


# --- Applications ---
class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    job_description: Optional[str] = Field(default=None, max_length=20_000)
    job_url: Optional[str] = Field(default=None, max_length=1_000)
    status: ApplicationStatus = "saved"
    match_score: Optional[float] = Field(default=None, ge=0, le=1)
    notes: Optional[str] = Field(default=None, max_length=5_000)

    strip_text = field_validator("company", "job_title", "job_description", "job_url", "notes", mode="before")(_strip_value)

    @field_validator("job_url")
    @classmethod
    def http_url_only(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.lower().startswith(("http://", "https://")):
            raise ValueError("Job link must start with http:// or https://")
        return v or None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = Field(default=None, max_length=5_000)
    match_score: Optional[float] = Field(default=None, ge=0, le=1)


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    job_title: str
    job_description: Optional[str] = None
    job_url: Optional[str] = None
    status: str
    match_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[dt.datetime] = None
    updated_at: Optional[dt.datetime] = None


# --- Job search ---
class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    tags: list[str]
    job_type: Optional[str] = None
    salary: Optional[str] = None
    posted_at: Optional[str] = None
    snippet: str
    description: str
    relevance: Optional[float] = None


class JobSearchResponse(BaseModel):
    jobs: list[JobListing]
    ranked_by_resume: bool
    sources: list[str]
    unavailable_sources: list[str]


# --- Chat assistant ---
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    strip_text = field_validator("message", mode="before")(_strip_value)


class ChatResponse(BaseModel):
    reply: str
