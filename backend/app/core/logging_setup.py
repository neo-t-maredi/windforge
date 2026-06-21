# logging_setup.py
# Structured logging configuration for WindForge API.
# Uses structlog to produce JSON-formatted logs suitable for ingestion
# by log aggregation tools (e.g. ELK, Datadog, CloudWatch Logs) in a
# production deployment. Falls back to readable console output in dev.

import logging
import sys
import structlog
from app.core.config import settings


def configure_logging():
    """
    Configure structlog for the application. Call once at startup
    from main.py before the FastAPI app is created.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.APP_ENV == "production":
        # JSON output for production — machine-parseable
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable colored output for local development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


logger = structlog.get_logger("windforge")