"""Scores how well a resume matches a job description.

Two signals, combined:
- Semantic: the job description and resume are split into chunks and each
  job chunk is paired with its most similar resume chunk. (Embedding the
  whole resume as one string doesn't work - the model truncates input at
  ~256 tokens, so only the top of the resume would ever be compared.)
- Skills: a keyword vocabulary with aliases ("k8s" -> kubernetes) gives an
  actionable matched/missing list and a coverage ratio.
"""
import re

import numpy as np

from app.services.embeddings import embed_texts
from app.utils.chunking import chunk_text

# canonical skill -> extra spellings that count as the same skill
SKILLS: dict[str, list[str]] = {
    # Languages
    "python": [], "java": [], "javascript": ["js", "es6"], "typescript": ["ts"],
    "c++": ["cpp"], "c#": ["csharp"], "go": ["golang"], "rust": [], "kotlin": [], "swift": [],
    "php": [], "ruby": [], "scala": [], "r": ["r programming", "rstudio"], "matlab": [], "bash": ["shell scripting"],
    "sql": [], "nosql": [], "html": ["html5"], "css": ["css3"],
    # Frontend
    "react": ["react.js", "reactjs"], "next.js": ["nextjs"], "vue": ["vue.js", "vuejs"],
    "angular": ["angularjs"], "redux": [], "tailwind": ["tailwindcss"], "bootstrap": [],
    # Backend
    "node.js": ["node", "nodejs"], "express": ["express.js"], "fastapi": [], "django": [],
    "flask": [], "spring boot": ["spring"], ".net": ["dotnet", "asp.net"], "graphql": [],
    "rest api": ["rest apis", "restful", "rest"], "microservices": [], "grpc": [],
    # Data stores
    "postgresql": ["postgres"], "mysql": [], "mongodb": ["mongo"], "redis": [], "sqlite": [],
    "elasticsearch": [], "dynamodb": [], "oracle": [], "snowflake": [], "bigquery": [],
    # Cloud / DevOps
    "aws": ["amazon web services"], "gcp": ["google cloud"], "azure": [], "docker": [],
    "kubernetes": ["k8s"], "terraform": [], "ansible": [], "jenkins": [], "github actions": [],
    "ci/cd": ["cicd", "continuous integration"], "linux": [], "git": ["github", "gitlab"],
    "nginx": [], "serverless": ["aws lambda"],
    # Data / ML
    "machine learning": ["ml"], "deep learning": [], "nlp": ["natural language processing"],
    "computer vision": [], "pytorch": [], "tensorflow": [], "keras": [], "scikit-learn": ["sklearn"],
    "pandas": [], "numpy": [], "spark": ["pyspark", "apache spark"], "hadoop": [], "airflow": [],
    "llm": ["llms", "large language models"], "rag": ["retrieval augmented generation"],
    "langchain": [], "generative ai": ["genai", "gen ai"], "faiss": [], "embeddings": [],
    "vector database": ["vector databases", "vector db"], "data analysis": ["data analytics"],
    "statistics": [], "power bi": ["powerbi"], "tableau": [], "excel": ["ms excel", "microsoft excel"],
    "etl": [], "data visualization": [],
    # Testing / practice
    "unit testing": ["pytest", "jest", "junit"], "selenium": [], "agile": [], "scrum": [], "jira": [],
    "system design": [], "data structures": ["dsa"], "algorithms": [], "oop": ["object oriented programming"],
    # Non-technical
    "communication": ["communication skills"], "leadership": [], "project management": [],
    "stakeholder management": [], "problem solving": ["problem-solving"], "teamwork": ["collaboration"],
    "figma": [], "seo": [], "salesforce": [], "sap": [],
}

# Everyday English words that would cause false matches ("go to", "the rest
# of", "spring 2025"). They're only detected through their unambiguous
# spellings ("golang", "restful", "spring boot").
_AMBIGUOUS = {"r", "go", "rest", "spring", "lambda", "ts", "ml", "node"}

_PATTERNS: list[tuple[str, re.Pattern]] = [
    (canonical, re.compile(rf"(?<![\w+#.]){re.escape(term)}(?![\w+#])", re.IGNORECASE))
    for canonical, aliases in SKILLS.items()
    for term in [canonical, *aliases]
    if term not in _AMBIGUOUS
]


def extract_skills(text: str) -> set[str]:
    return {canonical for canonical, pattern in _PATTERNS if pattern.search(text)}


# Lists of alternatives - "C++, Java, or Python", "such as React or Vue",
# "(JavaScript, TypeScript, etc.)" - are one requirement satisfied by any member.
_ALTERNATIVE_PATTERNS = [
    re.compile(r"\(([^()]{3,300})\)"),
    re.compile(r"(?:such as|e\.g\.|e\.g|like|including|either)\s+([^.;:()\n]{3,300})", re.IGNORECASE),
    re.compile(r"((?:[^,.;:()\n]+,\s*)*[^,.;:()\n]+?,?\s+or\s+[^,.;:()\n]+)", re.IGNORECASE),
]


def _requirement_groups(job_description: str) -> list[set[str]]:
    """Splits the job's skills into requirements. Each requirement is a set of
    interchangeable skills; a plain skill is a one-element set."""
    groups: list[set[str]] = []
    for pattern in _ALTERNATIVE_PATTERNS:
        for match in pattern.finditer(job_description):
            skills = extract_skills(match.group(1))
            if len(skills) >= 2 and skills not in groups:
                groups.append(skills)
    # Drop groups that are strict subsets of a bigger alternative list.
    groups = [g for g in groups if not any(g < other for other in groups)]
    grouped = set().union(*groups) if groups else set()
    singles = [{skill} for skill in extract_skills(job_description) - grouped]
    return groups + singles


def _job_chunks(job_description: str) -> list[str]:
    """Job posts are often one long block; split into sentence groups."""
    chunks = chunk_text(job_description)
    pieces = []
    for chunk in chunks:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", chunk) if len(s.strip()) > 20]
        group, length = [], 0
        for sentence in sentences:
            group.append(sentence)
            length += len(sentence)
            if length >= 250:
                pieces.append(" ".join(group))
                group, length = [], 0
        if group:
            pieces.append(" ".join(group))
    return pieces[:40] or [job_description[:2000]]


def _calibrate(cosine: float) -> float:
    # MiniLM cosine for unrelated text is ~0.1-0.2 and for a near-verbatim
    # match ~0.85; map that band onto 0-1 so strong matches don't saturate.
    return float(np.clip((cosine - 0.15) / 0.7, 0.0, 1.0))


def _summary(score: float, missing: list[str]) -> str:
    if score >= 0.75:
        verdict = "Strong match - your resume lines up well with this role."
    elif score >= 0.55:
        verdict = "Good match - a few gaps worth addressing before you apply."
    elif score >= 0.35:
        verdict = "Partial match - tailor your resume to highlight relevant experience."
    else:
        verdict = "Weak match - this role asks for quite different experience."
    if missing:
        verdict += f" Consider covering: {', '.join(missing[:5])}."
    return verdict


def match_resume(resume_text: str, job_description: str) -> dict:
    resume_chunks = chunk_text(resume_text)[:60]
    job_chunks = _job_chunks(job_description)

    vectors = embed_texts(job_chunks + resume_chunks)
    job_vecs, resume_vecs = vectors[: len(job_chunks)], vectors[len(job_chunks):]
    # Rows: job requirements; take each requirement's best supporting resume chunk.
    best = (job_vecs @ resume_vecs.T).max(axis=1)
    semantic = _calibrate(float(best.mean()))

    resume_skills = extract_skills(resume_text)
    requirements = _requirement_groups(job_description)
    matched = sorted(set().union(*(g & resume_skills for g in requirements)) if requirements else set())
    unmet = [g for g in requirements if not g & resume_skills]
    # An unmet alternative list is shown as one gap: "go or rust".
    missing = sorted(" or ".join(sorted(g)) for g in unmet)
    coverage = (len(requirements) - len(unmet)) / len(requirements) if requirements else None

    score = semantic if coverage is None else 0.5 * semantic + 0.5 * coverage
    score = round(float(np.clip(score, 0.0, 1.0)), 3)
    return {
        "match_score": score,
        "semantic_score": round(semantic, 3),
        "skill_coverage": round(coverage, 3) if coverage is not None else None,
        "matched_skills": matched,
        "missing_skills": missing,
        "summary": _summary(score, missing),
    }
