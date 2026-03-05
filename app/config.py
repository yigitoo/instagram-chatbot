from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    meta_verify_token: str
    meta_page_access_token: str
    instagram_account_id: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    admin_pause_duration_minutes: int = 30

    model_config = {"env_file": ".env"}


settings = Settings()
