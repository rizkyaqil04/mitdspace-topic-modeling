import os
import re
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
async def scraping_data(title_per_page = 100, max_pages = 1): 
    logging.info("Starting scraping process")

    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    
    schema_links = {
        "name": "DSpace MIT Paper Links",
        "baseSelector": "div.ds-artifact-item",
        "fields": [
            {"name": "doi", "selector": "a[href]", "type": "attribute", "attribute": "href"} 
        ]
    }

    link_strategy = JsonCssExtractionStrategy(schema_links)
    detail_links = []

    schema = {
        "name": "DSpace MIT Papers",
        "baseSelector": "div.item-summary-view-metadata",
        "fields": [
            {"name": "title", "selector": "h2.page-header", "type": "text"},
            {"name": "abstract", "selector": "div.simple-item-view-description > div", "type": "text"},
            {"name": "authors", "selector": "div.simple-item-view-authors", "type": "text"},
            {"name": "journal_conference_name", "selector": "div.simple-item-view-journal:has(h5:-soup-contains('Journal')) > div", "type": "text"},
            {"name": "publisher", "selector": "div.simple-item-view-journal:has(h5:-soup-contains('Publisher')) > div", "type": "text"},
            {"name": "year", "selector": "div.simple-item-view-date", "type": "text"},
            {"name": "doi", "selector": "div.simple-item-view-uri a", "type": "attribute", "attribute": "href"} 
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    all_papers = []

    logging.info("Stage 1: Collecting detail URLs...")

    async with AsyncWebCrawler() as crawler:
        url = "https://dspace.mit.edu/discover"

        for page in range(1, max_pages + 1):
            logging.info(f"Scraping page {page}...")

            js_code = []
            wait_for = None

            if page == 1:
                js_code = [
                    "document.querySelector('a[href*=\"sort_by=dc.date.issued_dt\"][href*=\"order=desc\"]')?.click();",
                    "await new Promise(resolve => setTimeout(resolve, 10000));",
                    f"document.querySelector('a[href*=\\\"rpp={title_per_page}\\\"]')?.click();",
                    "await new Promise(resolve => setTimeout(resolve, 10000));"
                ]
                wait_for = "div.ds-artifact-item"

            elif page > 1:
                js_code = ["document.querySelector('a.next-page-link')?.click();"]
                wait_for = "div.ds-artifact-item"


            try:
                result = await crawler.arun(
                    url=url,
                    config=CrawlerRunConfig(
                        cache_mode=CacheMode.BYPASS,
                        extraction_strategy=link_strategy,
                        js_code=js_code,
                        wait_for=wait_for,
                        page_timeout=120_000
                    )
                )

                links = json.loads(result.extracted_content)
                for link in links:
                    if link.get("doi", "").startswith("/handle/"):
                        link["doi"] = "https://dspace.mit.edu" + link["doi"]
                detail_links.extend(links)

                logging.info(f"Page {page}: Scraped {len(links)} links")

            except Exception as e:
                logging.error(f"Error scraping page {page}: {str(e)}")
                break



        # Step 2: 
        
        js_code = [
            "showAuthors();"
        ]

        for item in detail_links:
            url = item["doi"]
            try:
                result = await crawler.arun(url=url, config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=extraction_strategy,
                    # js_code = js_code,
                    page_timeout=120_000
                ))
                papers = json.loads(result.extracted_content)

                # Process Post-Scraping (Cleaning)
                for paper in papers:
                    # Fix author list
                    if isinstance(paper.get("authors"), str):
                        raw_authors = paper["authors"]

                        # Remove the 'Author(s)' prefix and any "Show more / less" garbage
                        raw_authors = re.sub(r"^Author\(s\)\s*", "", raw_authors)
                        raw_authors = re.sub(r"...Show\s*more.*$", "", raw_authors, flags=re.DOTALL)

                        authors_list = []
                        for item in raw_authors.split(";"):
                            name = item.strip()
                            if "," in name:
                                last, first = name.split(",", 1)
                                authors_list.append(first.strip() + " " + last.strip())
                            elif name:
                                authors_list.append(name.strip())

                        paper["authors"] = authors_list

                    # Fix year: extract only year from date
                    if "year" in paper and isinstance(paper["year"], str):
                        match = re.search(r"\d{4}", paper["year"])
                        if match:
                            paper["year"] = match.group(0) 

                    # Fix DOI
                    if paper.get("doi") and paper["doi"].startswith("/handle/"):
                        paper["doi"] = "dspace.mit.edu" + paper["doi"]

                    # Compose clean paper dict in desired field order
                    cleaned_paper = {
                        "title": paper.get("title", ""),
                        "abstract": paper.get("abstract", ""),
                        "authors": paper.get("authors", []),
                        "journal_conference_name": paper.get("journal_conference_name", "No Journal/Conference"),
                        "publisher": paper.get("publisher", "No Publisher"),
                        "year": paper.get("year", ""),
                        "doi": paper.get("doi", ""),
                        "group_name": "Cireng Crispy"
                    }

                    all_papers.append(cleaned_paper)

                # all_papers.extend(papers)
                logging.info(f"Page {page}: Scraped {len(papers)} papers")
            except Exception as e:
                logging.error(f"Error scraping page {page}: {str(e)}")


    # Save to JSON
    data_path = f"data/raw/mit_scraped_{title_per_page * max_pages}.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=4)

    logging.info(f"Scraped data saved to {data_path}, total papers: {len(all_papers)}")
    
    return all_papers

if __name__ == "__main__":
    import asyncio
    asyncio.run(scraping_data())
