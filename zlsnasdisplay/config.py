#! /usr/bin/env python3

"""
Centralized configuration management for ZlsNasDisplay.

This module provides a single source of truth for all environment variables
and configuration settings used throughout the application.
"""

import os
from typing import Optional


class Config:
    """Application configuration loaded from environment variables."""

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Sentry error tracking
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")

    # Display configuration
    DISPLAY_IMAGE_PATH: Optional[str] = os.getenv("DISPLAY_IMAGE_PATH")

    # Web dashboard configuration
    ENABLE_WEB_DASHBOARD: bool = os.getenv("ENABLE_WEB_DASHBOARD", "false").lower() in (
        "true",
        "1",
        "yes",
    )
    WEB_DASHBOARD_HOST: str = os.getenv("WEB_DASHBOARD_HOST", "0.0.0.0")
    WEB_DASHBOARD_PORT: int = int(os.getenv("WEB_DASHBOARD_PORT", "8000"))

    # Web dashboard advanced settings
    WEB_METRICS_UPDATE_INTERVAL: int = int(os.getenv("WEB_METRICS_UPDATE_INTERVAL", "2"))  # seconds
    WEB_CACHE_TTL_INTERNET: int = int(os.getenv("WEB_CACHE_TTL_INTERNET", "30"))  # seconds
    WEB_CACHE_TTL_SIGNAL: int = int(os.getenv("WEB_CACHE_TTL_SIGNAL", "30"))  # seconds
    WEB_CACHE_TTL_IP: int = int(os.getenv("WEB_CACHE_TTL_IP", "300"))  # seconds
    WEB_THREAD_POOL_WORKERS: int = int(os.getenv("WEB_THREAD_POOL_WORKERS", "3"))

    # Display renderer cache settings
    DISPLAY_CACHE_TTL_INTERNET: int = int(os.getenv("DISPLAY_CACHE_TTL_INTERNET", "30"))  # seconds
    DISPLAY_CACHE_TTL_SIGNAL: int = int(os.getenv("DISPLAY_CACHE_TTL_SIGNAL", "60"))  # seconds
    DISPLAY_CACHE_TTL_IP: int = int(os.getenv("DISPLAY_CACHE_TTL_IP", "300"))  # seconds

    # Display update timeout
    DISPLAY_UPDATE_TIMEOUT: int = int(os.getenv("DISPLAY_UPDATE_TIMEOUT", "30"))  # seconds

    # Historical data retention (for graphs)
    HISTORY_MAX_ENTRIES: int = int(
        os.getenv("HISTORY_MAX_ENTRIES", "1800")
    )  # 1 hour at 2s intervals

    @classmethod
    def is_root(cls) -> bool:
        """Check if running as root user."""
        return os.getuid() == 0
