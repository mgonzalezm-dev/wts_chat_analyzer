"""
Logging configuration
"""
import logging
import sys
from pythonjsonlogger import jsonlogger
from app.config import settings

def setup_logging():
    """Configure application logging"""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # Create formatter
    if settings.ENVIRONMENT == "production":
        # JSON formatter for production
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            fmt=settings.LOG_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Set specific log levels for libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)
    
    return logger