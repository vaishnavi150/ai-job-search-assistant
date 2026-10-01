"""Thin client for a locally running Ollama server. No API key needed -
just `ollama run <model>` (or `ollama serve`) on the machine running this
backend. Raises a clear, user-facing error if Ollama isn't reachable rather
than a raw connection traceback.
"""
import requests

from app.config import settings


class OllamaUnavailableError(RuntimeError):
    pass


def _post(path: str, payload: dict) -> dict:
    url = f"{settings.ollama_base_url}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError as exc:
        raise OllamaUnavailableError(
            f"Couldn't reach Ollama at {settings.ollama_base_url}. "
            f"Is it running? Try `ollama serve` and `ollama pull {settings.ollama_model}`."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise OllamaUnavailableError(
            f"Ollama returned an error - is the model '{settings.ollama_model}' pulled? "
            f"Try `ollama pull {settings.ollama_model}`. ({exc})"
        ) from exc


def generate(prompt: str, system: str | None = None) -> str:
    """Single-turn generation."""
    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    data = _post("/api/generate", payload)
    return data.get("response", "").strip()


def chat(messages: list[dict], system: str | None = None) -> str:
    """Multi-turn chat. `messages` is a list of {"role": "user"|"assistant", "content": ...}."""
    full_messages = ([{"role": "system", "content": system}] if system else []) + messages
    payload = {"model": settings.ollama_model, "messages": full_messages, "stream": False}
    data = _post("/api/chat", payload)
    return data.get("message", {}).get("content", "").strip()
