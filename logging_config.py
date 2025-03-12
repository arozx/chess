import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Generate a timestamp for the log file name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/chess_{timestamp}.log"


# Configure root logger
def configure_logging():
    """Configure logging to write to both file and console"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # File handler - writes everything to file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Console handler - only warnings and errors to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    # Add both handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Get logger instances
def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)
