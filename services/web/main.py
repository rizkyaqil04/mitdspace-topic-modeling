from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI()

SCRAPER_URL = "http://scraper:8000/scrape"
PREPROCESSOR_URL = "http://preprocessor:8000/preprocess"
TRAINER_URL = "http://trainer:8000/train"
TRAINER_RESULT_URL = "http://trainer:8000/result"
MONITORING_URL = "http://monitoring:8000/monitoring"

class ScrapeRequest(BaseModel):
    title_per_page: int = 100
    max_pages: int = 1

class PreprocessRequest(BaseModel):
    filename: str

@app.post("/scrape")
def trigger_scrape(req: ScrapeRequest):
    try:
        resp = requests.post(SCRAPER_URL, json=req.model_dump(), timeout=600000)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger scraping: {e}")

@app.post("/preprocess")
def trigger_preprocess(req: PreprocessRequest):
    try:
        resp = requests.post(PREPROCESSOR_URL, json=req.model_dump(), timeout=600)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger preprocessing: {e}")

@app.post("/train")
def trigger_train():
    try:
        resp = requests.post(TRAINER_URL, timeout=10)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger training: {e}")

@app.get("/result")
def get_train_result():
    try:
        resp = requests.get(TRAINER_RESULT_URL, timeout=10)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training result: {e}")

@app.get("/monitoring")
def get_train_result():
    try:
        resp = requests.get(MONITORING_URL, timeout=10)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get training result: {e}")