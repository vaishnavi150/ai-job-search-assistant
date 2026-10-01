import sys
import os
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fitz
from docx import Document

from app.services.resume_parser import extract_text


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extract_text_from_pdf():
    pdf_bytes = _make_pdf_bytes("Jane Doe - Python Developer")
    text = extract_text(pdf_bytes, "resume.pdf")
    assert "Jane Doe" in text
    assert "Python Developer" in text


def test_extract_text_from_docx():
    docx_bytes = _make_docx_bytes(["Jane Doe", "Python Developer with 5 years experience"])
    text = extract_text(docx_bytes, "resume.docx")
    assert "Jane Doe" in text
    assert "Python Developer" in text


def test_extract_text_from_txt():
    text = extract_text(b"Plain text resume content", "resume.txt")
    assert text == "Plain text resume content"


def test_extract_text_rejects_unsupported_format():
    try:
        extract_text(b"data", "resume.exe")
        assert False, "should have raised"
    except ValueError as exc:
        assert "Unsupported" in str(exc)
