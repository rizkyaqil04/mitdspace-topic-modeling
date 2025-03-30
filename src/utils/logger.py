import logging
import os
from pathlib import Path

LOGS_DIR = Path("logs")

def setup_logger(log_name):
    log_path = os.path.join(LOGS_DIR, f"{log_name}.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger(log_name)
