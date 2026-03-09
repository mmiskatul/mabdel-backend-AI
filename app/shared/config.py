from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mabdel backend AI"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    fernet_key: str = Field(default="_kv3sQkuAz8JZjhSUvWcJUR7mGmiVYc6goNO5dONUlc=")
    mongodb_uri: str = "mongodb://mongo:27017"
    mongodb_db_name: str = "mabdel_ai"
    redis_url: str = "redis://redis:6379/0"
    llm_provider: str = "stub"
    llm_api_key: str = "stub"
    llm_model: str = "stub-model"
    llm_api_base: str = "https://router.huggingface.co/v1"
    llm_timeout_seconds: float = 30.0
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Mabdel backend AI"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    admin_name: str = "SmartFlow Admin"
    admin_email: str = ""
    admin_password: str = ""
    signup_code_expire_minutes: int = 10
    signup_token_expire_minutes: int = 10
    otp_code_expire_minutes: int = 10
    reset_token_expire_minutes: int = 15
    websocket_path: str = "/ws"
    enable_auto_send_default: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
