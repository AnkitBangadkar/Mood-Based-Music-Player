import logging
import sys

# Create a custom logger
logger = logging.getLogger("MoodPlaylist")
logger.setLevel(logging.DEBUG)

# Add NullHandler by default (can be overridden)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

# Create formatters
c_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_logger(name):
    log = logging.getLogger(f"MoodPlaylist.{name}")
    # Ensure console handler is added for important loggers
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in log.handlers
    ):
        c_handler = logging.StreamHandler(sys.stdout)
        c_handler.setLevel(logging.INFO)
        c_handler.setFormatter(c_format)
        log.addHandler(c_handler)
    return log
