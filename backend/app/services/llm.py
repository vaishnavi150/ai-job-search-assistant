"""Thin LLM client. Two providers, picked by LLM_PROVIDER:

- "ollama": a locally running Ollama server. No API key needed - just
  `ollama run <model>` (or `ollama serve`) on the machine running this backend.
- "groq": Groq's hosted, OpenAI-compatible API. Needs GROQ_API_KEY. Used for
  cloud deploys (e.g. Render) where a local Ollama isn't available.

Raises a clear, user-facing error if the LLM isn't reachable rather than a
raw connection traceback.
"""
import requests

from app.config import settings


class LLMUnavailableError(RuntimeError):
    pass


# Kept so existing imports of the original name keep working.
OllamaUnavailableError = LLMUnavailableError


def _ollama_post(path: str, payload: dict) -> dict:
    url = f"{settings.ollama_base_url}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError as exc:
        raise LLMUnavailableError(
            f"Couldn't reach Ollama at {settings.ollama_base_url}. "
            f"Is it running? Try `ollama serve` and `ollama pull {settings.ollama_model}`."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise LLMUnavailableError(
            f"Ollama returned an error - is the model '{settings.ollama_model}' pulled? "
            f"Try `ollama pull {settings.ollama_model}`. ({exc})"
        ) from exc


def _groq_chat(messages: list[dict]) -> str:
    if not settings.groq_api_key:
        raise LLMUnavailableError("GROQ_API_KEY isn't set on the server.")
    try:
        resp = requests.post(
            f"{settings.groq_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={"model": settings.groq_model, "messages": messages},
            timeout=120,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise LLMUnavailableError(
            f"Groq returned an error for model '{settings.groq_model}': {exc.response.text[:300]}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise LLMUnavailableError(f"Couldn't reach Groq: {exc}") from exc
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate(prompt: str, system: str | None = None) -> str:
    """Single-turn generation."""
    if settings.llm_provider == "groq":
        messages = [{"role": "system", "content": system}] if system else []
        return _groq_chat(messages + [{"role": "user", "content": prompt}])

    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    data = _ollama_post("/api/generate", payload)
    return data.get("response", "").strip()


def chat(messages: list[dict], system: str | None = None) -> str:
    """Multi-turn chat. `messages` is a list of {"role": "user"|"assistant", "content": ...}."""
    full_messages = ([{"role": "system", "content": system}] if system else []) + messages
    if settings.llm_provider == "groq":
        return _groq_chat(full_messages)

    payload = {"model": settings.ollama_model, "messages": full_messages, "stream": False}
    data = _ollama_post("/api/chat", payload)
    return data.get("message", {}).get("content", "").strip()
