from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastAPI MongoDB Boilerplate"
    app_version: str = "0.1.0"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "mabdel_backend_ai"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

