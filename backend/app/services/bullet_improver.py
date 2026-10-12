"""Generates tailored resume bullets for a job description, grounded in
the user's actual resume via FAISS retrieval (the 'R' in RAG)."""
import re

from app.services import vector_store, llm

_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")

SYSTEM_PROMPT = (
    "You rewrite resume bullet points to match a job description. You must "
    "ONLY use experience, tools, and metrics present in the excerpts given "
    "to you - never invent skills, employers, or achievements. Output plain "
    "bullet points, one per line, starting with '-'. No preamble."
)


def improve_bullets(user_id: int, job_description: str, top_k: int = 5) -> dict:
    relevant_chunks = vector_store.search(user_id, job_description, top_k=top_k)
    if not relevant_chunks:
        return {"bullets": [], "grounded_on": [], "note": "No resume on file - upload one first."}

    context = "\n".join(f"- {c}" for c in relevant_chunks)
    prompt = f"""Job description:
{job_description}

Candidate's relevant resume excerpts:
{context}

Rewrite 3 resume bullet points that best match this job description, using \
only the experience above. Mirror the job description's language and \
priorities where the excerpts genuinely support it."""

    response_text = llm.generate(prompt, system=SYSTEM_PROMPT)
    # Keep only real bullet lines; drop any preamble the model adds anyway.
    bullets = [
        _BULLET_RE.sub("", line).replace("**", "").strip()
        for line in response_text.splitlines()
        if _BULLET_RE.match(line)
    ]
    if not bullets:  # model ignored the format - fall back to non-empty lines
        bullets = [line.replace("**", "").strip() for line in response_text.splitlines() if len(line.strip()) > 20]
    if not bullets:
        raise llm.LLMUnavailableError("The AI service returned an unusable response. Please try again.")
    return {"bullets": bullets[:6], "grounded_on": relevant_chunks}
