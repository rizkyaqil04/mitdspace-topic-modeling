from fastapi import APIRouter
from pathlib import Path
import json
import src.preprocessing.preprocessing as preprocessor

router = APIRouter()

SCRAPED_DATA_PATH = Path("data/raw/mit_scraped_10k.json")

@router.post("/preprocess")
def preprocess_data():
    """
    Membaca data hasil scraping dan menjalankan preprocessing serta feature extraction.
    """
    if not SCRAPED_DATA_PATH.exists():
        return {"error": f"Scraped data not found at {SCRAPED_DATA_PATH}"}

    papers = json.loads(SCRAPED_DATA_PATH.read_text(encoding="utf-8"))
    preprocessed_data = preprocessor.preprocess_papers(papers)

    texts = [paper["title"] for paper in preprocessed_data]
    preprocessor.compute_embeddings(texts)
    preprocessor.compute_tfidf(texts)

    return {
        "message": "Preprocessing & feature extraction completed.",
        # "num_processed": len(preprocessed_data)
    }
