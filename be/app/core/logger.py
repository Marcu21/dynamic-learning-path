import logging
import colorlog
import os
from logging.handlers import RotatingFileHandler

from app.core.config import settings

_logger_configured = False

def setup_logger():
    try:
        global _logger_configured
        if _logger_configured:
            return

        # Create log directory
        log_dir = os.path.abspath(settings.log_dir or "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file_path = os.path.join(log_dir, "app.log")
        log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

        # Formatters
        color_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s:%(name)s:%(reset)s %(message)s",
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bold_red',
            }
        )

        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        stream_handler = colorlog.StreamHandler()
        stream_handler.setFormatter(color_formatter)

        # Rotating file handler
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)

        # Root logger setup
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Remove previous handlers
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)

        # Add handlers
        root_logger.addHandler(stream_handler)
        root_logger.addHandler(file_handler)

        _logger_configured = True
    except Exception as e:
        print(f"Failed to configure logger: {e}")
        raise RuntimeError("Logger setup failed") from e


def get_logger(name: str = None):
    """
    Get a logger instance with the configured formatting.

    Args:
        name: Name for the logger. If None, uses the calling module's name.

    Returns:
        Logger instance
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')

    return logging.getLogger(name)


# Setup logger on import
setup_logger()