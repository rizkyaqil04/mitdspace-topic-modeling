import logging
import os
from pathlib import Path

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)  # Buat folder logs jika belum ada

def setup_logger(log_name):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Cegah log nyasar ke root logger

    # Cek supaya handler tidak ditambahkan dua kali
    if not logger.handlers:
        log_path = LOGS_DIR / f"{log_name}.log"
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

