import os
import re
import sys
import json
import logging
import asyncio
import random
from pathlib import Path
import time
from playwright.async_api import async_playwright
from prometheus_client import Counter, Summary

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

BASE_PATH = Path("app")
RAW_DATA_PATH = BASE_PATH.parent / "data" / "raw"
RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

#Logging configuration
logging.basicConfig(
    level=logging.INFO,  # Tampilkan level INFO dan di atasnya
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Arahkan ke stdout
)

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
extraction_strategy = JsonCssExtractionStrategy(schema, verbose=False)

scraped_papers_total = Counter(
    "scraped_papers_total", "Total number of papers scraped"
)
scraping_duration_seconds = Summary(
    "scraping_duration_seconds", "Time spent scraping papers"
)

async def scraping_data(title_per_page=10, max_pages=3):
    with scraping_duration_seconds.time():
        logging.info("Starting scraping process")
        collected_links = []

        async with async_playwright() as pw:
            start = time.time()
            
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
            page = await context.new_page()

            await page.goto("https://dspace.mit.edu/discover", wait_until="domcontentloaded")
            print(f"Page loaded: {time.time() - start:.2f} seconds")

            # Sort by date desc
            try:
                await page.click('button.dropdown-toggle')
                await page.wait_for_timeout(1000)
                await page.click('a[href*="sort_by=dc.date.issued_dt"][href*="order=desc"]')
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(8000)
            except Exception as e:
                print(f"Sort error: {e}")

            # Set rpp
            try:
                await page.click('button.dropdown-toggle')
                await page.wait_for_timeout(1000)
                await page.click(f'a[href*="rpp={title_per_page}"]')
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(8000)
            except Exception as e:
                print(f"RPP error: {e}")

            for current_page in range(1, max_pages + 1):
                try:
                    # Delay acak antar halaman (2.5 – 6.5 detik)
                    delay = random.uniform(2.5, 6.5)
                    print(f"[Page {current_page}] Sleeping for {delay:.2f} seconds...")
                    await page.wait_for_timeout(delay * 1000)

                    await page.wait_for_selector('div.ds-artifact-item', timeout=30000)
                    items = await page.query_selector_all('div.ds-artifact-item a[href]')
                    for a in items:
                        href = await a.get_attribute('href')
                        if href and "/handle/" in href:
                            full_link = "https://dspace.mit.edu" + href
                            if full_link not in collected_links:
                                collected_links.append(full_link)

                    print(f"✅ Page {current_page}: Collected {len(collected_links)} links so far")

                    next_btn = await page.query_selector('a.next-page-link')
                    if not next_btn:
                        break

                    # Validasi perubahan konten
                    prev_text = await page.locator('div.ds-artifact-item').first.inner_text()
                    await next_btn.click()
                    success = False

                    for _ in range(20):
                        await page.wait_for_timeout(1000)
                        try:
                            curr_text = await page.locator('div.ds-artifact-item').first.inner_text()
                            if curr_text != prev_text:
                                success = True
                                break
                        except Exception:
                            continue

                    if not success:
                        print("‼️ Timeout atau isi halaman tidak berubah setelah klik next.")
                        break

                    # Delay kecil setelah klik next
                    await page.wait_for_timeout(3000)

                except Exception as e:
                    print(f"Gagal klik next (page {current_page}): {e}")
                    break

            await browser.close()

        print(f"Total unique links collected: {len(set(collected_links))}")


        # Stage 2: Ambil detail isi
        all_papers = []

        async with AsyncWebCrawler(
            default_headers={
                "User-Agent": "Mozilla/5.0 (compatible; MyResearchBot/1.0; +http://example.com/botinfo)"
            }
        ) as crawler:
            for idx, url in enumerate(collected_links):
                try:
                    # Tambahkan delay acak antara 2.5–5 detik
                    delay = random.uniform(2.5, 5.0)
                    logging.info(f"Sleeping for {delay:.2f} seconds to avoid rate-limiting...")
                    await asyncio.sleep(delay)

                    result = await crawler.arun(
                        url=url,
                        config=CrawlerRunConfig(
                            cache_mode=CacheMode.BYPASS,
                            extraction_strategy=extraction_strategy,
                            page_timeout=120_000
                        )
                    )
                    papers = json.loads(result.extracted_content)
                    for paper in papers:
                        if isinstance(paper.get("authors"), str):
                            raw_authors = re.sub(r"^Author\(s\)\s*", "", paper["authors"])
                            raw_authors = re.sub(r"...Show\s*more.*$", "", raw_authors, flags=re.DOTALL)
                            authors_list = []
                            for name in raw_authors.split(";"):
                                name = name.strip()
                                if "," in name:
                                    last, first = name.split(",", 1)
                                    authors_list.append(f"{first.strip()} {last.strip()}")
                                elif name:
                                    authors_list.append(name)
                            paper["authors"] = authors_list

                        if "year" in paper and isinstance(paper["year"], str):
                            match = re.search(r"\d{4}", paper["year"])
                            if match:
                                paper["year"] = match.group(0)

                        if paper.get("doi") and paper["doi"].startswith("/handle/"):
                            paper["doi"] = "https://dspace.mit.edu" + paper["doi"]

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
                    logging.info(f"Detail {idx+1}/{len(collected_links)}: Scraped {len(papers)} papers")
                except Exception as e:
                    logging.error(f"Error scraping detail {idx+1}: {str(e)}")


        # Simpan hasil
        data_path = RAW_DATA_PATH / f"mit_scraped_{title_per_page * max_pages}.json"
        try:
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(all_papers, f, ensure_ascii=False, indent=4)
            logging.info(f"Scraped data saved to {data_path}, total papers: {len(all_papers)}")
        except Exception as e:
            logging.error(f"Failed to save scraped data: {e}")

        scraped_papers_total.inc(len(all_papers))
        return all_papers
