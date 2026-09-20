from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Full-Stack AI RAG Chatbot"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super_secret_jwt_key_for_development_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./chatbot.db"

    # Initial Admin Seed defaults
    INITIAL_ADMIN_EMAIL: str = "admin@example.com"
    INITIAL_ADMIN_PASSWORD: str = "AdminPassword123!"
    INITIAL_ADMIN_NAME: str = "System Administrator"

    # Groq Settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "groq/compound-mini"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
