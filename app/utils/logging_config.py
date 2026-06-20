"""
DevFlow Agent — Logging Configuration
Call setup_logging() once at application startup.
"""

import logging
import sys

_configured = False


def setup_logging(level: str = "INFO") -> None:
    """
    Configure application-wide logging to stdout.
    Safe to call multiple times — only configures once.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
    """
    global _configured
    if _configured:
        return

    log_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.setLevel(log_level)
    if not root.handlers:
        root.addHandler(handler)

    # Quieten noisy third-party libraries
    for noisy in ("httpx", "httpcore", "urllib3", "github", "werkzeug"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (thin convenience wrapper)."""
    return logging.getLogger(name)
