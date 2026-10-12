"""Thin LLM client. Two providers, picked by LLM_PROVIDER:

- "ollama": a locally running Ollama server. No API key needed - just
  `ollama run <model>` (or `ollama serve`) on the machine running this backend.
- "groq": Groq's hosted, OpenAI-compatible API. Needs GROQ_API_KEY. Used for
  cloud deploys (e.g. Render) where a local Ollama isn't available.

Failures raise LLMUnavailableError with a message that's safe to show users;
provider details (status codes, response bodies) go to the server log only.
"""
import logging

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    pass


# Kept so existing imports of the original name keep working.
OllamaUnavailableError = LLMUnavailableError

_GENERIC = "The AI service is temporarily unavailable. Please try again in a minute."


def _ollama_post(path: str, payload: dict) -> dict:
    url = f"{settings.ollama_base_url}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=settings.llm_timeout_seconds)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError as exc:
        logger.error("Ollama unreachable at %s", settings.ollama_base_url)
        raise LLMUnavailableError(
            "The local AI model isn't running. Start it with `ollama serve` "
            f"and `ollama pull {settings.ollama_model}`."
            if not settings.is_production else _GENERIC
        ) from exc
    except requests.exceptions.Timeout as exc:
        logger.error("Ollama timed out after %ss", settings.llm_timeout_seconds)
        raise LLMUnavailableError("The AI model took too long to respond. Please try again.") from exc
    except requests.exceptions.HTTPError as exc:
        logger.error("Ollama HTTP %s: %s", exc.response.status_code, exc.response.text[:300])
        raise LLMUnavailableError(
            f"The AI model returned an error - is '{settings.ollama_model}' pulled? "
            f"Try `ollama pull {settings.ollama_model}`."
            if not settings.is_production else _GENERIC
        ) from exc
    except ValueError as exc:
        logger.error("Ollama returned non-JSON response")
        raise LLMUnavailableError(_GENERIC) from exc


def _groq_chat(messages: list[dict]) -> str:
    if not settings.groq_api_key:
        logger.error("LLM_PROVIDER=groq but GROQ_API_KEY isn't set")
        raise LLMUnavailableError("AI features aren't configured on this server yet.")
    try:
        resp = requests.post(
            f"{settings.groq_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": messages,
                "max_completion_tokens": settings.llm_max_tokens,
            },
            timeout=settings.llm_timeout_seconds,
        )
    except requests.exceptions.Timeout as exc:
        logger.error("Groq timed out after %ss", settings.llm_timeout_seconds)
        raise LLMUnavailableError("The AI service took too long to respond. Please try again.") from exc
    except requests.exceptions.RequestException as exc:
        logger.error("Couldn't reach Groq: %s", type(exc).__name__)
        raise LLMUnavailableError(_GENERIC) from exc

    if resp.status_code == 429:
        logger.warning("Groq rate limit hit: %s", resp.text[:300])
        raise LLMUnavailableError("The AI service is busy right now (rate limit reached). Please try again shortly.")
    if resp.status_code >= 400:
        logger.error("Groq HTTP %s for model %s: %s", resp.status_code, settings.groq_model, resp.text[:500])
        raise LLMUnavailableError(_GENERIC)
    try:
        content = resp.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.error("Unexpected Groq response shape: %s", resp.text[:300])
        raise LLMUnavailableError(_GENERIC) from exc
    return _require_text(content)


def _require_text(content) -> str:
    text = (content or "").strip()
    if not text:
        # Don't hand the user an empty "result" as if it were real output.
        logger.error("LLM returned an empty response")
        raise LLMUnavailableError("The AI service returned an empty response. Please try again.")
    return text


def generate(prompt: str, system: str | None = None) -> str:
    """Single-turn generation."""
    if settings.llm_provider == "groq":
        messages = [{"role": "system", "content": system}] if system else []
        return _groq_chat(messages + [{"role": "user", "content": prompt}])

    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    data = _ollama_post("/api/generate", payload)
    return _require_text(data.get("response"))


def chat(messages: list[dict], system: str | None = None) -> str:
    """Multi-turn chat. `messages` is a list of {"role": "user"|"assistant", "content": ...}."""
    full_messages = ([{"role": "system", "content": system}] if system else []) + messages
    if settings.llm_provider == "groq":
        return _groq_chat(full_messages)

    payload = {"model": settings.ollama_model, "messages": full_messages, "stream": False}
    data = _ollama_post("/api/chat", payload)
    return _require_text(data.get("message", {}).get("content"))
