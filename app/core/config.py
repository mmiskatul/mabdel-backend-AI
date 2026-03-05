from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mabdel AI Backend"
    app_version: str = "0.1.0"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "mabdel_backend_ai"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    signup_validation_token_expire_minutes: int = 10
    otp_code_expire_minutes: int = 10
    reset_token_expire_minutes: int = 15
    expose_test_verification_code: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "Mabdel AI"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
