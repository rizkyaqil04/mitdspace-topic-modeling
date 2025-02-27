import os
import json
import logging
from urllib.parse import urljoin, urlencode
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Ensure Playwright is installed
install_status = ensure_playwright_installed()
if install_status is True:
    logging.info("Playwright installed.")
elif install_status is False:
    logging.error("Failed to install Playwright. Check your internet connection or try installing manually.")
else:
    logging.info("Playwright already installed.")

# Function to scrape the author profile
async def scrape_scholar_profiles(max_pages): 
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

    base_url = "https://scholar.google.com/citations"
    org_id = "16345133980181568013"
    params = {
        "view_op": "view_org",
        "hl": "id",
        "org": org_id
    }

    profile_schema = {
        "name": "Google Scholar MIT Profiles",
        "baseSelector": "div.gs_ai_t",
        "fields": [
            {"name": "name", "selector": "h3.gs_ai_name a", "type": "text"},
            {"name": "profile_link", "selector": "h3.gs_ai_name a", "type": "attribute", "attribute": "href"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(profile_schema, verbose=True)
    all_profiles = []
    next_page = None
    page_count = 0

    async with AsyncWebCrawler() as crawler:
        while page_count < max_pages:
            logging.info(f"Scraping page {page_count}")
            if next_page:
                params.update(next_page)

            url = f"{base_url}?{urlencode(params)}"
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=extraction_strategy
            )

            result = await crawler.arun(url=url, config=config)
            profiles = json.loads(result.extracted_content)
            all_profiles.extend(profiles)

            if not profiles:
                logging.warning("No profiles found on page {page_count}")
                break

            page_count += 1

    return all_profiles, max_pages

# Function to scrape authors publication
async def scrape_publications(profile_name, profile_url):
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    
    publication_schema = {
        "name": "Google Scholar Publications",
        "baseSelector": "tr.gsc_a_tr",
        "fields": [
            {"name": "title", "selector": "td.gsc_a_t a", "type": "text"},
            {"name": "year", "selector": "span.gsc_a_h.gsc_a_hc", "type": "text"}
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(publication_schema, verbose=True)

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
        )

        full_url = f"https://scholar.google.com{profile_url}"
        logging.info(f"Scraping publications for {profile_name} ({full_url})")
        result = await crawler.arun(url=full_url, config=config)
        publications = json.loads(result.extracted_content)

    formatted_publications = []
    for pub in publications:
        title = pub.get("title", "Unknown Title")
        year = pub.get("year", "Unknown")
        formatted_publications.append({
            "title": title,
            "author": profile_name,
            "year": year
        })

    return formatted_publications

async def scraping_data(max_pages=1):
    logging.info("Starting scholar scraping")
    profiles, max_pages = await scrape_scholar_profiles(max_pages)

    data_path = f"data/raw/scholar_scraped_{20 * max_pages * 10}.json"

    all_papers = []
    for profile in profiles:
        profile_name = profile["name"]
        profile_link = profile["profile_link"]
        
        logging.info(f"Scraping publications for {profile_name}")
        publications = await scrape_publications(profile_name, profile_link)
        all_papers.extend(publications)
    
    if not all_papers:
        logging.error("No data scraped! Something went wrong.")
    
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=4)
    
    logging.info(f"Scraped data saved to {data_path}")
    return all_papers

if __name__ == "__main__":
    import asyncio
    logging.info("Running scholar scraping script")
    asyncio.run(scraping_data())

