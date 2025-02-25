import os
import json
import logging

# Paths for storing scraping results
DATA_PATH = "data/raw/mit_scraped.json"
LOG_PATH = "logs/scraping.log"

# Ensure directories exist
os.makedirs("data/raw", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

async def get_max_pages():
    max_pages = 40  # Sesuaikan jumlah hamalan (1 halaman = 250 judul)
    logging.info(f"Max pages set to {max_pages}")
    return max_pages

async def scraping_data():
    logging.info("Starting scraping process")

    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    
    max_pages = await get_max_pages()
    
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
            url = f"https://dspace.mit.edu/discover?rpp=250&etal=0&group_by=none&page={page}&sort_by=dc.date.issued_dt&order=desc"
            logging.info(f"Scraping page {page}: {url}")
            try:
                result = await crawler.arun(url=url, config=config)
                papers = json.loads(result.extracted_content)
                all_papers.extend(papers)
                logging.info(f"Page {page}: Scraped {len(papers)} papers")
            except Exception as e:
                logging.error(f"Error scraping page {page}: {str(e)}")

    # Save to JSON
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=4)

    logging.info(f"Scraped data saved to {DATA_PATH}, total papers: {len(all_papers)}")
    print(f"Scraped data saved to {DATA_PATH}")
    return all_papers

if __name__ == "__main__":
    import asyncio
    asyncio.run(scraping_data())
