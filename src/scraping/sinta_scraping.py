import os
import re
import json
import logging
from datetime import datetime
from src.scraping.check_playwright import ensure_playwright_installed

# Paths for storing scraping results
LOG_PATH = "logs/scraping.log"

# Ensure directories exist
os.makedirs("data/raw", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure Playwright is installed
install_status = ensure_playwright_installed()
if install_status is True:
    logging.info("Playwright installed.")
elif install_status is False:
    logging.error("Failed to install Playwright. Check your internet connection or try installing manually.")
else:
    logging.info("Playwright already installed.")

# Function to get max pages
async def get_max_pages(query, max_pages): 
    logging.info(f"🔍 Mendeteksi jumlah halaman untuk query: {query}")

    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    
    schema = {
        "name": "Pagination Info",
        "baseSelector": "div.text-center.pagination-text",
        "fields": [
            {"name": "pagination", "selector": "small", "type": "text"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
        )

        url = f"https://sinta.kemdikbud.go.id/google?q={query.replace(' ', '+')}"
        
        try:
            result = await crawler.arun(url=url, config=config)
            pagination_text = json.loads(result.extracted_content)

            if pagination_text:
                match = re.search(r"Page \d+ of (\d+)", pagination_text[0]["pagination"])
                if match:
                    pages = int(match.group(1))
                    logging.info(f"📄 Ditemukan {pages} halaman untuk query '{query}'")

                    return max_pages if pages > max_pages else pages

        except Exception as e:
            logging.error(f"⚠️ Gagal mendapatkan jumlah halaman: {e}")

    return 1  # Default jika tidak ditemukan

# Function to scrape the papers
async def scraping_data(query, max_pages=20):
    logging.info(f"🚀 Memulai scraping data untuk query: {query}")

    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    
    max_pages = await get_max_pages(query, max_pages)
    data_path = f"data/raw/sinta_scraped_{10 * max_pages}.json"

    schema = {
        "name": "Sinta Papers",
        "baseSelector": "div.ar-list-item",
        "fields": [
            {"name": "title", "selector": "div.ar-title", "type": "text"},
            {"name": "description", "selector": "div.ar-meta", "type": "text"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    all_papers = []

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
        )

        for page in range(1, max_pages + 1):
            url = f"https://sinta.kemdikbud.go.id/google?page={page}&q={query.replace(' ', '+')}"
            logging.info(f"📡 Mengambil halaman {page} dari {max_pages}...")

            try:
                result = await crawler.arun(url=url, config=config)
                papers = json.loads(result.extracted_content)
                if papers:
                    logging.info(f"✅ {len(papers)} paper ditemukan di halaman {page}")
                all_papers.extend(papers)

            except Exception as e:
                logging.error(f"❌ Error saat scraping halaman {page}: {e}")


    # Simpan hasil scraping ke file JSON
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(all_papers, f, ensure_ascii=False, indent=4)
        logging.info(f"📁 Data scraping berhasil disimpan di {data_path}")

    except Exception as e:
        logging.error(f"❌ Gagal menyimpan file JSON: {e}")

    return all_papers

if __name__ == "__main__":
    import asyncio

    query = "machine learning"
    logging.info("🔥 Scraper dimulai...")
    
    start_time = datetime.now()
    asyncio.run(scraping_data(query))
    
    end_time = datetime.now()
    logging.info(f"🏁 Scraper selesai dalam {end_time - start_time}")

