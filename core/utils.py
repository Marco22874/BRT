"""
Utility functions module for BRT Shipping Management Application
Contains helper functions for logging, font selection, and other utilities
"""

import platform
import logging
from pathlib import Path
from datetime import datetime


def get_monospace_font() -> str:
    """
    Returns the appropriate monospaced font based on the operating system
    to avoid warnings for missing fonts

    Returns:
        str: The monospaced font name for the current platform
    """
    system = platform.system()

    if system == "Windows":
        return "Courier New"
    elif system == "Darwin":  # macOS
        return "Monaco"
    else:  # Linux and others
        return "Monospace"


def setup_logging() -> logging.Logger:
    """
    Configure the logging system for the application
    Creates a logger that writes to both file and console

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Log file path with date
    log_file = log_dir / f"brt_app_{datetime.now().strftime('%Y%m%d')}.log"

    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Create logger
    logger = logging.getLogger('BRTApp')
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # File handler - logs everything (DEBUG and above)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)

    # Console handler - logs only INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)

    return logger


# Cache of the monospaced font for global use
MONOSPACE_FONT = get_monospace_font()

# Initialize logger globally
logger = setup_logging()
