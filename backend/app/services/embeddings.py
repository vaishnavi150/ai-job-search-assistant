"""Wraps sentence-transformers so the model is loaded once and reused.
Downloads the model from Hugging Face on first run (needs internet the
first time only - it's cached locally after that)."""
import numpy as np

from app.config import settings

_model = None


class EmbeddingModelUnavailableError(RuntimeError):
    pass


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        try:
            _model = SentenceTransformer(settings.embedding_model)
        except Exception as exc:  # network error, no cached weights, etc.
            raise EmbeddingModelUnavailableError(
                f"Couldn't load the embedding model '{settings.embedding_model}'. "
                "It downloads from Hugging Face on first use, so this usually "
                "means no internet access on first run. Try again once you're "
                "online - after that it's cached locally in ~/.cache/huggingface."
            ) from exc
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (N, D) float32 array of L2-normalized embeddings, ready
    for cosine similarity via dot product / FAISS inner-product search."""
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.astype("float32")


def embed_text(text: str) -> np.ndarray:
    return embed_texts([text])[0]
