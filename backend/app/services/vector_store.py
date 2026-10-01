"""A small per-user FAISS index over resume chunks, persisted to disk. One
index per user, rebuilt whenever they re-upload a resume. This is the
retrieval half of the RAG pipeline used by bullet tailoring and the chat
assistant.
"""
import json
import os

import faiss
import numpy as np

from app.config import settings
from app.services.embeddings import embed_texts, embed_text

os.makedirs(settings.faiss_index_dir, exist_ok=True)


def _index_path(user_id: int) -> str:
    return os.path.join(settings.faiss_index_dir, f"user_{user_id}.index")


def _chunks_path(user_id: int) -> str:
    return os.path.join(settings.faiss_index_dir, f"user_{user_id}_chunks.json")


def build_index(user_id: int, chunks: list[str]) -> None:
    """(Re)builds the FAISS index for a user from scratch."""
    if not chunks:
        return
    vectors = embed_texts(chunks)  # (N, D), already L2-normalized
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)  # inner product on normalized vecs = cosine similarity
    index.add(vectors)

    faiss.write_index(index, _index_path(user_id))
    with open(_chunks_path(user_id), "w") as f:
        json.dump(chunks, f)


def has_index(user_id: int) -> bool:
    return os.path.exists(_index_path(user_id)) and os.path.exists(_chunks_path(user_id))


def search(user_id: int, query: str, top_k: int = 5) -> list[str]:
    """Returns the top_k most relevant resume chunks for the query
    (e.g. a job description), or [] if the user has no resume indexed."""
    if not has_index(user_id):
        return []

    index = faiss.read_index(_index_path(user_id))
    with open(_chunks_path(user_id)) as f:
        chunks = json.load(f)

    query_vec = np.expand_dims(embed_text(query), axis=0)
    k = min(top_k, len(chunks))
    _, indices = index.search(query_vec, k)
    return [chunks[i] for i in indices[0] if i != -1]


def delete_index(user_id: int) -> None:
    for path in (_index_path(user_id), _chunks_path(user_id)):
        if os.path.exists(path):
            os.remove(path)
