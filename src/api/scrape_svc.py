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
