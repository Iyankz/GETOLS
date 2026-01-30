"""
GETOLS Configuration Module
Handles all application configuration via environment variables.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="GETOLS", env="APP_NAME")
    app_version: str = Field(default="1.0.1", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(
        default="mysql+pymysql://getols:password@localhost:3306/getols_db",
        env="DATABASE_URL"
    )
    
    # Security
    secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        env="SECRET_KEY"
    )
    encryption_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        env="ENCRYPTION_KEY"
    )
    
    # Session
    session_lifetime: int = Field(default=60, env="SESSION_LIFETIME")  # minutes
    cookie_secure: bool = Field(default=False, env="COOKIE_SECURE")  # Set True for HTTPS
    cookie_httponly: bool = Field(default=True, env="COOKIE_HTTPONLY")
    cookie_samesite: str = Field(default="lax", env="COOKIE_SAMESITE")  # lax for HTTP compatibility
    
    # OLT Connection
    olt_connection_timeout: int = Field(default=10, env="OLT_CONNECTION_TIMEOUT")
    olt_command_timeout: int = Field(default=30, env="OLT_COMMAND_TIMEOUT")
    
    # SNMP
    snmp_timeout: int = Field(default=5, env="SNMP_TIMEOUT")
    snmp_retries: int = Field(default=3, env="SNMP_RETRIES")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience function
settings = get_settings()
