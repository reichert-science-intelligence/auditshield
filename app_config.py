# app_config.py
"""
AuditShield Phase 1 - Centralized configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_anthropic_client(api_key=None):
    """
    Get Anthropic client without proxies parameter.
    HuggingFace Spaces sets HTTP_PROXY/HTTPS_PROXY which causes
    TypeError with httpx 0.28+ (proxies kwarg removed). Using
    trust_env=False avoids reading proxy env vars.
    """
    import httpx
    from anthropic import Anthropic

    http_client = httpx.Client(trust_env=False)
    return Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"), http_client=http_client)


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
