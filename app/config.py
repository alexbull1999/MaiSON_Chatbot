from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import Optional

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
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # External Service URLs
    auth_service_url: str = "http://localhost:8001"
    property_service_url: str = "http://localhost:8002"
    availability_service_url: str = "http://localhost:8003"

    # API Base URLs
    police_uk_api_base_url: str = os.getenv("POLICE_UK_API_BASE_URL", "https://data.police.uk/api")
    ons_api_base_url: str = os.getenv("ONS_API_BASE_URL", "https://api.ons.gov.uk")

    # Cache Settings
    cache_ttl: int = 3600  # 1 hour
    max_cache_items: int = 1000

    # Rate Limiting
    osm_rate_limit: int = 2  # requests per second
    police_uk_rate_limit: float = 0.5  # Max 30 requests per minute
    ons_rate_limit: int = 30  # requests per minute

    # Search Parameters
    default_search_radius: int = int(os.getenv("DEFAULT_SEARCH_RADIUS", "1000"))  # in meters
    max_search_radius: float = 5.0  # kilometers

    # Feature Flags
    use_google_maps: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Debug: Print API keys (masked)
        if self.google_api_key:
            masked_key = f"{self.google_api_key[:4]}...{self.google_api_key[-4:]}"
            print(f"Debug: Loaded Google API key from env: {masked_key}")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields


settings = Settings() 