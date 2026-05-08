from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://hometask:hometask@localhost:5432/hometask"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM provider: "none" (template fallback) | "gigachat" | "ollama"
    LLM_PROVIDER: str = "none"
    # GigaChat — base64(ClientId:ClientSecret) from Sberbank developer portal
    GIGACHAT_AUTH_KEY: str = ""
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Embedding provider: "tfidf" (default, pure Python) | "sentence-transformers"
    # Set to "sentence-transformers" after installing requirements-ai.txt
    EMBEDDING_PROVIDER: str = "tfidf"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # VAPID keys for Web Push notifications (run scripts/generate_vapid.py to create)
    # VAPID_PRIVATE_KEY: base64-encoded PEM private key
    # VAPID_PUBLIC_KEY: base64url uncompressed EC public key (sent to browser)
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "admin@hometask.local"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",   # silently ignore unknown env vars (client_id, client_secret, etc.)
    )


settings = Settings()
