from fastapi import FastAPI
from pydantic import BaseModel
import asyncio, argparse
from scraping import scraping_data

app = FastAPI()

class ScrapeRequest(BaseModel):
    title_per_page: int = 100
    max_pages: int = 1

class ScrapeResponse(BaseModel):
    message: str
    num_records: int

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(req: ScrapeRequest):
    try:
        papers = await scraping_data(req.title_per_page, req.max_pages)
        return {
            "message": f"Scraping complete. {len(papers)} papers scraped.",
            "num_records": len(papers)
        }
    except Exception as e:
        return {"message": str(e), "num_records": 0}

def main():
    parser = argparse.ArgumentParser(description="Scrape data from DSpace MIT")
    parser.add_argument("--title_per_page", type=int, default=100, help="Number of titles per page")
    parser.add_argument("--max_pages", type=int, default=1, help="Maximum number of pages to scrape")
    args = parser.parse_args()

    try:
        asyncio.run(scraping_data(args.title_per_page, args.max_pages))
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        
if __name__ == "__main__":
    main()