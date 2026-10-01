"""Scores how well a resume matches a job description using sentence
embeddings (semantic similarity, not just keyword overlap), plus a
keyword-based skill gap list that's easy for a user to act on."""
import re

import numpy as np

from app.services.embeddings import embed_texts

_SKILL_VOCAB = [
    "python", "java", "javascript", "typescript", "sql", "nosql", "react",
    "vue", "angular", "fastapi", "django", "flask", "node", "aws", "gcp",
    "azure", "docker", "kubernetes", "ci/cd", "postgres", "mysql", "mongodb",
    "pytorch", "tensorflow", "machine learning", "llm", "rag", "nlp",
    "rest api", "graphql", "git", "linux", "terraform", "microservices",
    "agile", "scrum", "faiss", "embeddings", "vector database",
]


def _extract_skills(text: str) -> set[str]:
    text_lower = text.lower()
    return {skill for skill in _SKILL_VOCAB if re.search(rf"\b{re.escape(skill)}\b", text_lower)}


def match_resume(resume_text: str, job_description: str) -> dict:
    vectors = embed_texts([resume_text, job_description])
    # Both vectors are L2-normalized, so dot product = cosine similarity.
    score = float(np.dot(vectors[0], vectors[1]))
    score = max(0.0, min(1.0, score))  # clamp for floating point noise

    resume_skills = _extract_skills(resume_text)
    job_skills = _extract_skills(job_description)

    return {
        "match_score": round(score, 3),
        "matched_skills": sorted(resume_skills & job_skills),
        "missing_skills": sorted(job_skills - resume_skills),
    }
