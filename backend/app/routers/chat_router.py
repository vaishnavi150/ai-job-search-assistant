from fastapi import APIRouter, Depends, HTTPException

from app.models import User
from app.schemas import ChatRequest, ChatResponse
from app.auth.dependencies import get_current_user
from app.services import vector_store, llm
from app.services.llm import OllamaUnavailableError
from app.services.embeddings import EmbeddingModelUnavailableError

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = (
    "You are a helpful, direct career advisor. Answer questions about job "
    "searching, resumes, interviews, and career strategy. If resume context "
    "is provided below, ground advice in it; otherwise answer generally and "
    "suggest the user upload a resume for more specific help."
)


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        relevant_chunks = vector_store.search(current_user.id, payload.message, top_k=3)
    except EmbeddingModelUnavailableError:
        relevant_chunks = []  # degrade gracefully - chat still works without resume grounding
    context = ""
    if relevant_chunks:
        context = "\n\nRelevant resume context:\n" + "\n".join(f"- {c}" for c in relevant_chunks)

    try:
        reply = llm.generate(payload.message + context, system=SYSTEM_PROMPT)
    except OllamaUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return ChatResponse(reply=reply)
