import re


def chunk_text(text: str) -> list[str]:
    """Splits resume text into coherent chunks (one role, one skills block,
    etc.) by blank lines, falling back to sentence grouping if the resume
    has no blank-line structure (common with PDF extraction)."""
    raw = [c.strip() for c in re.split(r"\n\s*\n", text.strip()) if c.strip()]
    if len(raw) >= 3:
        return raw

    # Fallback: PDF extraction often collapses everything into one blob.
    # Group into ~300 character chunks on line breaks instead.
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    chunks, current = [], []
    current_len = 0
    for line in lines:
        current.append(line)
        current_len += len(line)
        if current_len >= 300:
            chunks.append("\n".join(current))
            current, current_len = [], 0
    if current:
        chunks.append("\n".join(current))
    return chunks or [text.strip()]
