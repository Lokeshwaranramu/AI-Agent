"""
Centralized logging configuration for the AI Agent.
Uses loguru for structured, colorized logging.
"""
import os
import sys
from loguru import logger


def setup_logger() -> "logger":
    """
    Configure and return the application logger.

    Returns:
        Configured loguru logger instance
    """
    log_level = os.getenv("LOG_LEVEL", "INFO")

    # Remove default handler
    logger.remove()

    # Console handler with color
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True,
    )

    # File handler for persistent logs
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/agent_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    )

    return logger


log = setup_logger()
