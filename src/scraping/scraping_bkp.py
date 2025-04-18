import os
import json
import logging
import subprocess
import shutil
from datetime import datetime
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
            {"name": "abstract", "selector": "div.abstract", "type": "text"},
            {"name": "author", "selector": "span.author", "type": "text"},
            {"name": "publisher", "selector": "span.publisher", "type": "text"},
            {"name": "year", "selector": "span.date", "type": "text"},
            {"name": "doi", "selector": "a[href]", "type": "attribute", "attribute": "href"} 
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

                # Process Post-Scraping (Cleaning)
                for paper in papers:
                    # Fix author list
                    if isinstance(paper.get("author"), str):
                        raw_authors = paper["author"]
                        authors_list = []
                        for item in raw_authors.split(";"):
                            name = item.strip()
                            if "," in name:
                                last, first = name.split(",", 1)
                                authors_list.append(first.strip() + " " + last.strip())
                            elif name:
                                authors_list.append(name.strip())
                        paper["author"] = authors_list

                    # Fix year: extract only year from date
                    if "year" in paper and isinstance(paper["year"], str):
                        try:
                            paper["year"] = str(datetime.strptime(paper["year"], "%Y-%m-%d").year)
                        except ValueError:
                            pass  # biarin aja kalau format aneh
                    
                    # Fix DOI
                    if paper.get("doi") and paper["doi"].startswith("/handle/"):
                        paper["doi"] = "dspace.mit.edu" + paper["doi"]

                    # Default publisher
                    if not paper.get("publisher"):
                        paper["publisher"] = "No Publisher"

                    # Set group name
                    paper["group_name"] = "Cireng Crispy"

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
