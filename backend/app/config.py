import os
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "AI-Powered Pantry Recipe Assistant"
    API_V1_STR: str = "/api/v1"
    
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    PARQUET_PATH: Path = PROCESSED_DATA_DIR / "recipes.parquet"
    SQLITE_INDEX_PATH: Path = PROCESSED_DATA_DIR / "ingredient_index.sqlite"
    METADATA_DB_PATH: Path = PROCESSED_DATA_DIR / "recipe_metadata.sqlite"
    
    # Recommendation engine configuration (Milestone 2 baseline)
    IMS_WEIGHT: float = float(os.getenv("IMS_WEIGHT", "0.6"))
    PUS_WEIGHT: float = float(os.getenv("PUS_WEIGHT", "0.4"))
    DEFAULT_RECOMMENDATION_LIMIT: int = int(os.getenv("DEFAULT_RECOMMENDATION_LIMIT", "10"))
    MAX_RECOMMENDATION_LIMIT: int = int(os.getenv("MAX_RECOMMENDATION_LIMIT", "100"))
    CANDIDATE_POOL_LIMIT: int = int(os.getenv("CANDIDATE_POOL_LIMIT", "150"))
    
    # Personalization layer configuration (Milestone 3)
    CUISINE_BONUS_HIGH_CONFIDENCE: float = float(os.getenv("CUISINE_BONUS_HIGH_CONFIDENCE", "15.0"))
    CUISINE_BONUS_MEDIUM_CONFIDENCE: float = float(os.getenv("CUISINE_BONUS_MEDIUM_CONFIDENCE", "10.0"))
    TIME_BONUS_MAX: float = float(os.getenv("TIME_BONUS_MAX", "10.0"))
    TIME_PENALTY_RATE: float = float(os.getenv("TIME_PENALTY_RATE", "0.2"))
    TIME_PENALTY_MAX: float = float(os.getenv("TIME_PENALTY_MAX", "15.0"))
    
    # Milestone 6 AI-Assisted Grounded Recipe Guidance & Structured RAG Layer
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    LLM_API_KEY: str = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "600"))

    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
