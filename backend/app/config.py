import logging
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    secret_key: str = _DEV_SECRET
    # Short-ish sessions: there are no refresh tokens, so this is how long a
    # stolen token stays useful. Password changes revoke tokens immediately.
    access_token_expire_minutes: int = 480
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./ai_job_assistant.db"

    # "ollama" (local, no key) or "groq" (hosted, OpenAI-compatible API)
    llm_provider: str = "ollama"
    llm_timeout_seconds: int = 90
    llm_max_tokens: int = 1500

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_cache_dir: str = ".fastembed_cache"
    faiss_index_dir: str = "faiss_indexes"

    # Comma-separated, e.g. "http://localhost:5173,https://my-app.onrender.com"
    frontend_origin: str = "http://localhost:5173"
    # Where password-reset links point. Defaults to the first FRONTEND_ORIGIN.
    frontend_url: str = ""

    # --- Email (password reset) ---
    # "brevo" (HTTP API - works on Render's free tier, which blocks SMTP ports),
    # "smtp" (any SMTP server - local dev or paid hosts), or "" (disabled).
    email_provider: str = ""
    email_from: str = ""
    email_from_name: str = "AI Job Search Assistant"
    brevo_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    password_reset_token_minutes: int = 30

    # --- Limits ---
    max_upload_mb: int = 5
    job_cache_minutes: int = 360

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=("settings_",))

    @field_validator("embedding_model")
    @classmethod
    def qualify_embedding_model(cls, v: str) -> str:
        # .env files from v0.1 use the bare sentence-transformers name, which
        # fastembed only accepts with its organisation prefix.
        return f"sentence-transformers/{v}" if v == "all-MiniLM-L6-v2" else v

    @property
    def sqlalchemy_database_url(self) -> str:
        # Some hosts hand out postgres:// URLs, which SQLAlchemy 2 no longer accepts.
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.database_url

    @property
    def frontend_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.frontend_origin.split(",") if o.strip()]

    @property
    def public_frontend_url(self) -> str:
        if self.frontend_url:
            return self.frontend_url.rstrip("/")
        return self.frontend_origins[0] if self.frontend_origins else "http://localhost:5173"

    @property
    def is_production(self) -> bool:
        # Render sets RENDER=true on every service.
        return os.environ.get("RENDER", "").lower() == "true" or os.environ.get("ENVIRONMENT") == "production"

    @property
    def email_enabled(self) -> bool:
        if self.email_provider == "brevo":
            return bool(self.brevo_api_key and self.email_from)
        if self.email_provider == "smtp":
            return bool(self.smtp_host and self.email_from)
        return False


settings = Settings()

if settings.is_production and settings.secret_key == _DEV_SECRET:
    raise RuntimeError("SECRET_KEY must be set to a long random value in production.")
if settings.is_production and len(settings.secret_key) < 32:
    # Not fatal, so an existing deploy with a short key keeps running.
    logging.getLogger(__name__).warning("SECRET_KEY is shorter than 32 characters; use a longer random value.")
