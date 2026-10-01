import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.chunking import chunk_text


def test_chunk_text_splits_on_blank_lines():
    text = "Experience\nBackend Engineer at Acme\n\nSkills\nPython, SQL, AWS\n\nEducation\nB.S. CS"
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert "Backend Engineer" in chunks[0]
    assert "Python" in chunks[1]


def test_chunk_text_falls_back_for_unstructured_text():
    long_line = "word " * 200  # no blank lines at all
    chunks = chunk_text(long_line)
    assert len(chunks) >= 1
    assert all(isinstance(c, str) and c for c in chunks)
