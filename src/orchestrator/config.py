from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Agent LLM Orchestration Platform"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    default_timeout_seconds: int = 30
    memory_db_path: str = "./data/agent_memory.db"
    max_concurrent_jobs: int = 8
    enable_fake_tool_results: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
