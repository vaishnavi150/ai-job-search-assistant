"""Generates interview questions from a job description, and drives a
stateless mock-interview chat (the client sends conversation history back
each turn; nothing is persisted server-side for this starter)."""
from app.services import llm

QUESTIONS_SYSTEM_PROMPT = (
    "You generate realistic technical and behavioral interview questions "
    "based on a job description. Output one question per line, no numbering, "
    "no preamble, no extra commentary."
)

MOCK_INTERVIEW_SYSTEM_PROMPT = (
    "You are a professional but friendly technical interviewer conducting a "
    "mock interview for the role described below. Ask one question at a "
    "time. After the candidate answers, give brief, specific, constructive "
    "feedback (2-3 sentences) on their answer, then ask the next question. "
    "Keep the whole interview to around 5-6 questions covering both "
    "technical and behavioral areas relevant to the role. If this is the "
    "first message (empty history), just ask the opening question - do not "
    "give feedback yet."
)


def generate_questions(job_description: str, num_questions: int = 5) -> list[str]:
    prompt = (
        f"Job description:\n{job_description}\n\n"
        f"Generate {num_questions} interview questions for this role - a mix "
        f"of technical and behavioral."
    )
    response_text = llm.generate(prompt, system=QUESTIONS_SYSTEM_PROMPT)
    questions = [
        line.strip().lstrip("-1234567890.").strip()
        for line in response_text.splitlines()
        if line.strip()
    ]
    return questions[:num_questions]


def mock_interview_reply(job_description: str, history: list[dict]) -> str:
    system = f"{MOCK_INTERVIEW_SYSTEM_PROMPT}\n\nJob description:\n{job_description}"
    if not history:
        return llm.chat([{"role": "user", "content": "Please begin the interview."}], system=system)
    return llm.chat(history, system=system)
