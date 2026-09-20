from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TOGETHER_AI_API_KEY: Optional[str] = None
    FIREWORKS_AI_API_KEY: Optional[str] = None
    MISTRAL_AI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    PDF_DIR: str = "../../dataset"
    RESULTS_DIR: str = "./results"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()
