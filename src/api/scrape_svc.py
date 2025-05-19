from fastapi import APIRouter
import src.scraping.scraping as scraper
from pathlib import Path
import json
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("scraping_svc")

@router.post("/scrape")
async def scrape_data():
    """
    Menjalankan proses scraping dan menyimpan hasilnya ke file JSON.
    """
    try:
        logger.info("Memulai proses scraping...")
        scraped_data = await scraper.scraping_data(250, 40)

        logger.info(f"Scraping selesai. Jumlah data: {len(scraped_data)}")
        return {
            "message": "Scraping completed successfully.",
            "num_records": len(scraped_data),
        }
    except Exception as e:
        logger.exception("Terjadi kesalahan saat scraping.")
        return {"error": str(e)}
