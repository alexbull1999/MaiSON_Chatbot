from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./chatbot.db"
    
    # Security
    secret_key: str = "your-secret-key"
    service_secret_key: str = "dev-secret-key"
    
    # LLM API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    
    # External Service URLs
    auth_service_url: str = "http://localhost:8001"
    property_service_url: str = "http://localhost:8002"
    availability_service_url: str = "http://localhost:8003"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug: Print API keys (masked)
        if self.google_api_key:
            masked_key = f"{self.google_api_key[:4]}...{self.google_api_key[-4:]}"
            print(f"Debug: Loaded Google API key from env: {masked_key}")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 