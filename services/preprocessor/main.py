from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
from preprocessing import preprocess_papers
import logging

app = FastAPI()

# === konfigurasi ===
BASE_PATH = Path("app")
RAW_DATA_DIR = BASE_PATH.parent / "data" / "raw"

# === models ===
class PreprocessRequest(BaseModel):
    filename: str  # Contoh: "mit_scraped_1000.json"

class PreprocessResponse(BaseModel):
    message: str
    num_records: int

# === endpoint ===
@app.post("/preprocess", response_model=PreprocessResponse)
def preprocess_endpoint(req: PreprocessRequest):
    file_path = RAW_DATA_DIR / req.filename

    if not file_path.exists():
        return {"message": f"File '{req.filename}' not found.", "num_records": 0}
    
    try:
        papers = json.loads(file_path.read_text(encoding="utf-8"))
        processed_papers = preprocess_papers(papers)
        return {
            "message": f"Preprocessing complete. {len(processed_papers)} papers processed.",
            "num_records": len(processed_papers)
        }
    except Exception as e:
        logging.error(f"Error in preprocess_endpoint: {e}")
        return {"message": str(e), "num_records": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
