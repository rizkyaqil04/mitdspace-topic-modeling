from fastapi import APIRouter
import json
from pathlib import Path

from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("show_data_preprocessed_svc")

PREPROCESSED_DATA_PATH = Path("data/processed/data_preprocessed.json")

@router.get("/data-processed")
async def get_preprocessed_data():
    """
    Mengembalikan hasil preprocessing dalam bentuk JSON.
    """
    try:
        if PREPROCESSED_DATA_PATH.exists():
            logger.info(f"Membaca data dari {PREPROCESSED_DATA_PATH}")
            with open(PREPROCESSED_DATA_PATH, "r") as f:
                data = json.load(f)
            logger.info(f"Data preprocessing berhasil dimuat. Jumlah record: {len(data)}")
            return {"preprocessed_data": data}
        else:
            logger.warning("File hasil preprocessing tidak ditemukan.")
            return {"error": "Preprocessed data not found"}
    except Exception as e:
        logger.exception("Terjadi kesalahan saat membaca data preprocessing.")
        return {"error": str(e)}

