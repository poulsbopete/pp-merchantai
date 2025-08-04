import os
import logging
from pydantic_settings import BaseSettings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings"""
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_username: str = ""
    elasticsearch_password: str = ""
    elasticsearch_index: str = "paypal-merchants"
    elasticsearch_use_ssl: bool = True
    elasticsearch_cloud_id: str = ""
    
    # Application settings
    app_title: str = "PayPal Merchant Troubleshooting"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Analysis thresholds
    conversion_rate_threshold: float = 0.1  # 10% drop threshold
    error_rate_threshold: float = 0.1  # 10% error threshold
    min_transaction_count: int = 100  # Minimum transactions for analysis
    
    # LLM settings
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4"
    demo_mode: bool = True
    
    class Config:
        env_file = ".env"  # Load .env file

settings = Settings()

# Debug logging to see what values are being loaded
logger.info(f"Environment variables:")
logger.info(f"ELASTICSEARCH_HOST from env: {os.getenv('ELASTICSEARCH_HOST', 'NOT_SET')}")
logger.info(f"ELASTICSEARCH_USERNAME from env: {os.getenv('ELASTICSEARCH_USERNAME', 'NOT_SET')[:20] if os.getenv('ELASTICSEARCH_USERNAME') else 'NOT_SET'}")
logger.info(f"ELASTICSEARCH_PORT from env: {os.getenv('ELASTICSEARCH_PORT', 'NOT_SET')}")
logger.info(f"ELASTICSEARCH_INDEX from env: {os.getenv('ELASTICSEARCH_INDEX', 'NOT_SET')}")

logger.info(f"Settings values:")
logger.info(f"elasticsearch_host: {settings.elasticsearch_host}")
logger.info(f"elasticsearch_username: {settings.elasticsearch_username[:20] if settings.elasticsearch_username else 'NOT_SET'}")
logger.info(f"elasticsearch_port: {settings.elasticsearch_port}")
logger.info(f"elasticsearch_index: {settings.elasticsearch_index}") 