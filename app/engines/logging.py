import logging
import sys
from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict
import logging.handlers
import os
import functools
import asyncio

# Create logs directory relative to this file's parent (project root)
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging format
class CustomFormatter(logging.Formatter):
    """
    Custom formatter that includes timestamp, level, module, and structured data
    """
    def format(self, record: logging.LogRecord) -> str:
        # Create a dict with the basic log information
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }

        # Add extra fields if they exist
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Add exception info if it exists
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging(
    level: str = "INFO",
    log_file: str = "app.log",
    max_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup application-wide logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of the log file
        max_size: Maximum size of each log file in bytes
        backup_count: Number of backup files to keep
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers = []

    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / log_file,
        maxBytes=max_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(CustomFormatter())
    logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Name of the logger (usually __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)

class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class
    """
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger

def log_function_call(func):
    """
    Decorator to log function calls with parameters and return values
    Handles both sync and async functions.
    """
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        call_details = {
            "function": func.__name__,
            "args": str(args),
            "kwargs": str(kwargs)
        }
        logger.debug(f"Calling {func.__name__}", extra={"extra_data": call_details})
        try:
            result = func(*args, **kwargs)
            logger.debug(
                f"Completed {func.__name__}",
                extra={"extra_data": {"result": str(result)}}
            )
            return result
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}",
                exc_info=True,
                extra={"extra_data": {"error": str(e)}}
            )
            raise

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        call_details = {
            "function": func.__name__,
            "args": str(args),
            "kwargs": str(kwargs)
        }
        logger.debug(f"Calling {func.__name__}", extra={"extra_data": call_details})
        try:
            result = await func(*args, **kwargs)
            logger.debug(
                f"Completed {func.__name__}",
                extra={"extra_data": {"result": str(result)}}
            )
            return result
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}",
                exc_info=True,
                extra={"extra_data": {"error": str(e)}}
            )
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper