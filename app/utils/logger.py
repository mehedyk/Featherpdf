"""
utils/logger.py
Minimal logging wrapper -- avoids pulling in any external logging library.
"""
import logging
import os
import sys

_LOG_DIR = os.path.join(os.path.expanduser("~"), ".featherpdf")
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")


def get_logger(name="featherpdf"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(file_handler)
    except Exception:
        pass  # if we can't write logs, don't crash the app over it

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)

    return logger
