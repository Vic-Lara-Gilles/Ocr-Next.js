from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	GEMINI_API_KEY: str
	DATABASE_URL: str
	REDIS_URL: str
	MAX_SYNC_PAGES: int = 5
	TEMP_DIR: str = "/tmp/ocr_uploads"

	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	return Settings()


settings = get_settings()
