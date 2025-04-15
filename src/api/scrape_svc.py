<<<<<<< HEAD
from fastapi import FastAPI
import src.scraping.scraping as scraper
import src.preprocessing.preprocessing as preprocessor

app = FastAPI()

@app.post("/scrape")
async def scrape_data():
    """
    Scraping otomatis dari MIT dan langsung menyimpan hasilnya.
    Setelah itu, langsung menjalankan preprocessing.
    """
    # Jalankan proses scraping MIT
    scraped_data = await scraper.scraping_data(10, 1)

    # Jalankan preprocessing
    preprocessed_data = preprocessor.preprocess_papers(scraped_data)

    return {"message": "Scraping & preprocessing completed"}
=======
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
>>>>>>> Aqill's
