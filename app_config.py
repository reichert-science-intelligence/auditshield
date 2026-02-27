# app_config.py
"""
AuditShield Phase 1 - Centralized configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # Database
    DB_TYPE = os.getenv("DB_TYPE", "sqlite")
    DATABASE_URL = os.getenv("DATABASE_URL")
    SQLITE_PATH = os.getenv("SQLITE_PATH", "auditshield.db")

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # App settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # CMS Parameters
    CMS_BASE_RATE_2026 = 1142.50
    RADV_ERROR_THRESHOLD = 5.0  # 5%

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return True
