from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)