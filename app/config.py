from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    paypal_env: str = "SANDBOX"
    paypal_client_id: str
    paypal_client_secret: str
    database_url: str = "sqlite:///./exhibit.db"
    paypal_webhook_id: str = ""
    sync_interval_seconds: int = 120


settings = Settings()
if settings.paypal_env != "SANDBOX":
    raise RuntimeError("PAYPAL_ENV must be SANDBOX. This project never touches live PayPal.")