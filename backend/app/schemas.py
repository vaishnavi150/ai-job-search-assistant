from typing import Optional
from pydantic import BaseModel, EmailStr


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Resume ---
class ResumeOut(BaseModel):
    filename: str
    raw_text: str

    class Config:
        from_attributes = True


# --- Matching ---
class MatchRequest(BaseModel):
    job_description: str


class MatchResponse(BaseModel):
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]


class BulletRequest(BaseModel):
    job_description: str


class BulletResponse(BaseModel):
    bullets: list[str]
    grounded_on: list[str]


# --- Interview ---
class InterviewQuestionsRequest(BaseModel):
    job_description: str
    num_questions: int = 5


class InterviewQuestionsResponse(BaseModel):
    questions: list[str]


class ChatTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class MockInterviewRequest(BaseModel):
    job_description: str
    history: list[ChatTurn] = []


class MockInterviewResponse(BaseModel):
    reply: str


# --- Applications ---
class ApplicationCreate(BaseModel):
    company: str
    job_title: str
    job_description: Optional[str] = None
    status: str = "saved"
    match_score: Optional[float] = None
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    match_score: Optional[float] = None


class ApplicationOut(BaseModel):
    id: int
    company: str
    job_title: str
    status: str
    match_score: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# --- Chat assistant ---
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
