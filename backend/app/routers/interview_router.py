from fastapi import APIRouter, Depends, HTTPException

from app.models import User
from app.schemas import (
    InterviewQuestionsRequest, InterviewQuestionsResponse,
    MockInterviewRequest, MockInterviewResponse,
)
from app.auth.dependencies import get_current_user
from app.services import interview
from app.services.llm import OllamaUnavailableError

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/questions", response_model=InterviewQuestionsResponse)
def questions(payload: InterviewQuestionsRequest, current_user: User = Depends(get_current_user)):
    try:
        qs = interview.generate_questions(payload.job_description, payload.num_questions)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return InterviewQuestionsResponse(questions=qs)


@router.post("/mock", response_model=MockInterviewResponse)
def mock(payload: MockInterviewRequest, current_user: User = Depends(get_current_user)):
    history = [turn.model_dump() for turn in payload.history]
    try:
        reply = interview.mock_interview_reply(payload.job_description, history)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return MockInterviewResponse(reply=reply)
