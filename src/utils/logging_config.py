"""
Logging configuration for IR Companion.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config import get_config


def setup_logging(
    log_file: Optional[Path] = None,
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        log_file: Optional file path for logging
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured root logger
    """
    config = get_config()
    log_level = level or config.logging.level

    # Create formatter
    formatter = logging.Formatter(
        fmt=config.logging.format,
        datefmt=config.logging.date_format,
    )

    # Configure root logger
    root_logger = logging.getLogger("ir_companion")
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.

    Args:
        name: Logger name (typically module name)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"ir_companion.{name}")
