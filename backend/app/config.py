from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... your existing settings ...
    CODE_EXECUTOR_URL: str = "http://code-executor:8080"
    MAX_CODE_EXECUTION_TIME: int = 10
    ALLOWED_LANGUAGES: list = ["python", "javascript", "java", "cpp", "go"]
    
    class Config:
        env_file = ".env"

settings = Settings()