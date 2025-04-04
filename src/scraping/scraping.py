import os
import json
import logging
import subprocess
import shutil
from src.utils.logger import setup_logger

# Ensure directories exist
os.makedirs("data/raw", exist_ok=True)

# Configure Logging
logger = setup_logger("scraping")

# Ensure Playwright is installed
def ensure_playwright_installed():
    """Memeriksa dan menginstal Playwright jika belum tersedia."""
    if shutil.which("playwright") is None:
        try:
            subprocess.run(["python", "-m", "pip", "install", "--upgrade", "playwright"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["python", "-m", "playwright", "install"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True  
        except subprocess.CalledProcessError:
            return False  
    return None

install_status = ensure_playwright_installed()
if install_status is True:
    logging.info("Playwright installed.")
elif install_status is False:
    logging.error("Failed to install Playwright. Check your internet connection or try installing manually.")
else:
    logging.info("Playwright already installed.")

# Scraping function
async def scraping_data(title_per_page = 100, max_pages = 5): 
    logging.info("Starting scraping process")

    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    
    max_pages = max_pages
    title_per_page = title_per_page
    data_path = f"data/raw/mit_scraped_{title_per_page * max_pages}.json"
    
    schema = {
        "name": "DSpace MIT Papers",
        "baseSelector": "div.ds-artifact-item",
        "fields": [
            {"name": "title", "selector": "h4.artifact-title", "type": "text"},
            {"name": "author", "selector": "span.ds-dc_contributor_author-authority", "type": "text", "multiple": True},
            {"name": "publisher", "selector": "span.publisher", "type": "text"},
            {"name": "date", "selector": "span.date", "type": "text"},
            {"name": "abstract", "selector": "div.abstract", "type": "text"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    all_papers = []

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
            page_timeout=120_000
        )

        for page in range(1, max_pages + 1):
            url = f"https://dspace.mit.edu/discover?rpp={title_per_page}&etal=0&group_by=none&page={page}&sort_by=dc.date.issued_dt&order=desc"
            logging.info(f"Scraping page {page}: {url}")
            try:
                result = await crawler.arun(url=url, config=config)
                papers = json.loads(result.extracted_content)
                all_papers.extend(papers)
                logging.info(f"Page {page}: Scraped {len(papers)} papers")
            except Exception as e:
                logging.error(f"Error scraping page {page}: {str(e)}")

    # Save to JSON
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=4)

    logging.info(f"Scraped data saved to {data_path}, total papers: {len(all_papers)}")
    
    return all_papers

if __name__ == "__main__":
    import asyncio
    asyncio.run(scraping_data())
