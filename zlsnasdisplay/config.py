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

    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of warnings."""
        warnings = []

        # Port validation
        if cls.WEB_DASHBOARD_PORT < 1024 and cls.ENABLE_WEB_DASHBOARD:
            warnings.append(
                f"WEB_DASHBOARD_PORT={cls.WEB_DASHBOARD_PORT} < 1024 requires root privileges"
            )
        if cls.WEB_DASHBOARD_PORT > 65535:
            warnings.append(f"WEB_DASHBOARD_PORT={cls.WEB_DASHBOARD_PORT} is invalid (max 65535)")

        # Timeout validation
        if cls.DISPLAY_UPDATE_TIMEOUT > 60:
            warnings.append(
                f"DISPLAY_UPDATE_TIMEOUT={cls.DISPLAY_UPDATE_TIMEOUT}s is very high (> 60s)"
            )
        if cls.DISPLAY_UPDATE_TIMEOUT < 5:
            warnings.append(
                f"DISPLAY_UPDATE_TIMEOUT={cls.DISPLAY_UPDATE_TIMEOUT}s is very low (< 5s)"
            )

        # Interval validation
        if cls.WEB_METRICS_UPDATE_INTERVAL < 1:
            warnings.append(
                f"WEB_METRICS_UPDATE_INTERVAL={cls.WEB_METRICS_UPDATE_INTERVAL}s is too low (min 1s)"
            )
        if cls.WEB_METRICS_UPDATE_INTERVAL > 60:
            warnings.append(
                f"WEB_METRICS_UPDATE_INTERVAL={cls.WEB_METRICS_UPDATE_INTERVAL}s is very high (> 60s)"
            )

        # Thread pool validation
        if cls.WEB_THREAD_POOL_WORKERS < 1:
            warnings.append(
                f"WEB_THREAD_POOL_WORKERS={cls.WEB_THREAD_POOL_WORKERS} is invalid (min 1)"
            )
        if cls.WEB_THREAD_POOL_WORKERS > 20:
            warnings.append(
                f"WEB_THREAD_POOL_WORKERS={cls.WEB_THREAD_POOL_WORKERS} is very high (> 20)"
            )

        # Cache TTL validation
        if cls.WEB_CACHE_TTL_INTERNET < 5:
            warnings.append(
                f"WEB_CACHE_TTL_INTERNET={cls.WEB_CACHE_TTL_INTERNET}s may cause excessive network checks"
            )

        # Log level validation
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_levels:
            warnings.append(
                f"LOG_LEVEL='{cls.LOG_LEVEL}' is invalid. Valid: {', '.join(valid_levels)}"
            )

        # History size validation
        if cls.HISTORY_MAX_ENTRIES > 10000:
            warnings.append(
                f"HISTORY_MAX_ENTRIES={cls.HISTORY_MAX_ENTRIES} may use excessive memory (> 10000)"
            )

        return warnings
