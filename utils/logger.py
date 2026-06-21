"""Logging utility for NOVA."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    FORMATS = {
        logging.DEBUG: Colors.CYAN + '%(levelname)s' + Colors.RESET + ' - %(name)s - %(message)s',
        logging.INFO: Colors.GREEN + '%(levelname)s' + Colors.RESET + ' - %(name)s - %(message)s',
        logging.WARNING: Colors.YELLOW + '%(levelname)s' + Colors.RESET + ' - %(name)s - %(message)s',
        logging.ERROR: Colors.RED + '%(levelname)s' + Colors.RESET + ' - %(name)s - %(message)s',
        logging.CRITICAL: Colors.BOLD + Colors.RED + '%(levelname)s' + Colors.RESET + ' - %(name)s - %(message)s',
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with colored console output and optional file logging.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging to file
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default settings.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
