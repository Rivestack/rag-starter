from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"

    # Search settings
    top_k: int = 10
    similarity_threshold: float = 0.1

    # HN ingestion settings
    hn_min_score: int = 10
    hn_days_to_keep: int = 30
    hn_max_comments_per_story: int = 20
    embedding_batch_size: int = 50

    model_config = {"env_file": ".env"}


settings = Settings()
