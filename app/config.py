import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration management class."""

    # API Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL: str = os.getenv(
        "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
    )
    OPENROUTER_HTTP_REFERER: str = os.getenv(
        "OPENROUTER_HTTP_REFERER", "https://github.com/your-username/rag-system"
    )
    OPENROUTER_APP_TITLE: str = os.getenv("OPENROUTER_APP_TITLE", "RAG System")

    # Database Configuration
    CHROMADB_PATH: str = os.getenv("CHROMADB_PATH", "./chroma_db")

    # Model Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    MODEL_SLUG: str = os.getenv("MODEL_SLUG", "openai/gpt-3.5-turbo")

    # Application Configuration
    APP_NAME: str = os.getenv("APP_NAME", "RAG System API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Limits and Thresholds
    MAX_DOCUMENT_LENGTH: int = int(os.getenv("MAX_DOCUMENT_LENGTH", "50000"))
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "20"))
    MAX_CHAT_RESULTS: int = int(os.getenv("MAX_CHAT_RESULTS", "10"))

    # Performance Configuration
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist."""
        Path(cls.CHROMADB_PATH).mkdir(parents=True, exist_ok=True)

    @classmethod
    def is_api_key_configured(cls) -> bool:
        """Check if OpenRouter API key is properly configured."""
        return bool(
            cls.OPENROUTER_API_KEY
            and cls.OPENROUTER_API_KEY != "your_openrouter_api_key_here"
        )


config = Config()

OPENROUTER_API_KEY = config.OPENROUTER_API_KEY
CHROMADB_PATH = config.CHROMADB_PATH
EMBEDDING_MODEL = config.EMBEDDING_MODEL
MODEL_SLUG = config.MODEL_SLUG
