from fastapi import APIRouter
import src.scraping.scraping as scraper
from pathlib import Path
import json

router = APIRouter()

@router.post("/scrape")
async def scrape_data():
    """
    Menjalankan proses scraping dan menyimpan hasilnya ke file JSON.
    """
    scraped_data = await scraper.scraping_data(10, 1)

    return {
        "message": "Scraping completed successfully.",
        "num_records": len(scraped_data),
    }
