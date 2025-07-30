import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    elasticsearch_host: str = os.getenv("ELASTICSEARCH_HOST", "localhost")
    elasticsearch_port: int = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    elasticsearch_username: str = os.getenv("ELASTICSEARCH_USERNAME", "")
    elasticsearch_password: str = os.getenv("ELASTICSEARCH_PASSWORD", "")
    elasticsearch_index: str = os.getenv("ELASTICSEARCH_INDEX", "paypal-merchants")
    elasticsearch_use_ssl: bool = os.getenv("ELASTICSEARCH_USE_SSL", "true").lower() == "true"
    elasticsearch_cloud_id: str = os.getenv("ELASTICSEARCH_CLOUD_ID", "")
    
    # Application settings
    app_title: str = "PayPal Merchant Troubleshooting"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Analysis thresholds
    conversion_rate_threshold: float = 0.1  # 10% drop threshold
    error_rate_threshold: float = 0.1  # 10% error threshold
    min_transaction_count: int = 100  # Minimum transactions for analysis
    
    class Config:
        env_file = ".env"

settings = Settings() 