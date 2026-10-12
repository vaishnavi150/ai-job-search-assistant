"""Wraps fastembed so the model is loaded once and reused. fastembed runs
the same sentence-transformers models (all-MiniLM-L6-v2 by default) on ONNX
Runtime instead of PyTorch, which keeps memory low enough for small hosts
like Render's free tier. Downloads the model on first use - run
`python -m app.services.embeddings` to pre-download it (the Render build
does this)."""
import logging

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)
_model = None


class EmbeddingModelUnavailableError(RuntimeError):
    pass


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        try:
            _model = TextEmbedding(
                model_name=settings.embedding_model,
                cache_dir=settings.embedding_cache_dir,
            )
        except Exception as exc:  # network error, no cached weights, etc.
            logger.error("Embedding model load failed: %s", exc)
            raise EmbeddingModelUnavailableError(
                f"Couldn't load the embedding model '{settings.embedding_model}'. "
                "It downloads on first use, so this usually means no internet "
                "access on first run. Try again once you're online - after that "
                f"it's cached locally in {settings.embedding_cache_dir}."
            ) from exc
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (N, D) float32 array of L2-normalized embeddings, ready
    for cosine similarity via dot product / FAISS inner-product search."""
    model = _get_model()
    embeddings = np.array(list(model.embed(texts)), dtype="float32")
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / np.clip(norms, 1e-12, None)


def embed_text(text: str) -> np.ndarray:
    return embed_texts([text])[0]


if __name__ == "__main__":
    _get_model()
    print(f"Embedding model '{settings.embedding_model}' ready.")
