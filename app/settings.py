from pydantic import BaseModel


class Settings(BaseModel):
    admin_username: str = "admin"
    admin_password: str = "admin123"
    session_cookie_name: str = "session"
    default_api_key: str = "test-api-key"


settings = Settings()