from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    azure_postgres_host: str = os.getenv("AZURE_POSTGRES_HOST", "")
    azure_postgres_user: str = os.getenv("AZURE_POSTGRES_USER", "")
    azure_postgres_password: str = os.getenv("AZURE_POSTGRES_PASSWORD", "")
    azure_postgres_db: str = os.getenv("AZURE_POSTGRES_DB", "postgres")
    azure_postgres_port: str = os.getenv("AZURE_POSTGRES_PORT", "5432")
    
    # Security
    secret_key: str = "your-secret-key"
    service_secret_key: str = "dev-secret-key"
    
    # LLM API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: str = os.getenv("GOOGLE_API_KEY")
    
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