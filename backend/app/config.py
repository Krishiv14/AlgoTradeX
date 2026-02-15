"""
Configuration settings for AlgoTradeX platform
Loads environment variables and provides app-wide settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "AlgoTradeX"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/algotrader"
    DATABASE_ECHO: bool = False  # Set to True to see SQL queries in logs
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:8501",  # Streamlit default port
        "http://localhost:3000",  # React default port
        "https://*.streamlit.app",  # Streamlit Cloud
    ]
    
    # Trading
    DEFAULT_INITIAL_CAPITAL: float = 100000.0  # ₹1 Lakh
    TRANSACTION_COST_PERCENT: float = 0.05  # 0.05% per trade (brokerage + taxes)
    
    # Data Sources
    YFINANCE_DELAY: float = 1.0  # Delay between API calls (seconds)
    MAX_WORKERS: int = 5  # Parallel downloads
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    # Redis (Optional - for caching)
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "algotrader.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
