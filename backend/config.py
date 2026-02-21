"""
Application configuration management.

Loads settings from environment variables with sensible defaults.
Separates config into Development and Production profiles.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    DATA_DIR = BASE_DIR / "data"
    PRODUCTS_FILE = DATA_DIR / "products.json"


class DevelopmentConfig(Config):
    """Development-specific configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production-specific configuration."""

    DEBUG = False
    TESTING = False


def get_config():
    """Return the appropriate config based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    return configs.get(env, DevelopmentConfig)
