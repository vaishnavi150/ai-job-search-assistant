"""Generates tailored resume bullets for a job description, grounded in
the user's actual resume via FAISS retrieval (the 'R' in RAG)."""
from app.services import vector_store, llm

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
    bullets = [
        line.strip().lstrip("-").strip()
        for line in response_text.splitlines()
        if line.strip().lstrip("-").strip()
    ]
    return {"bullets": bullets, "grounded_on": relevant_chunks}
