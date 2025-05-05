from fastapi import APIRouter
from pathlib import Path
import json
import src.preprocessing.preprocessing as preprocessor
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("preprocessing_svc")

SCRAPED_DATA_PATH = Path("data/raw/mit_scraped_1000.json")

@router.post("/preprocess")
def preprocess_data():
    """
    Membaca data hasil scraping dan menjalankan preprocessing serta feature extraction.
    """
    try:
        if not SCRAPED_DATA_PATH.exists():
            logger.warning(f"Scraped data not found at {SCRAPED_DATA_PATH}")
            return {"error": f"Scraped data not found at {SCRAPED_DATA_PATH}"}

        logger.info(f"Loading scraped data from {SCRAPED_DATA_PATH}")
        papers = json.loads(SCRAPED_DATA_PATH.read_text(encoding="utf-8"))

        logger.info("Starting preprocessing of papers.")
        preprocessed_data = preprocessor.preprocess_papers(papers)
        logger.info(f"Preprocessing complete. {len(preprocessed_data)} papers processed.")

        texts = [paper["title"] for paper in preprocessed_data]

        logger.info("Starting embedding computation.")
        preprocessor.compute_embeddings(texts)
        logger.info("Embeddings computed and saved.")

        logger.info("Starting TF-IDF computation.")
        preprocessor.compute_tfidf(texts)
        logger.info("TF-IDF vectors computed and saved.")

        return {
            "message": "Preprocessing & feature extraction completed.",
            "num_processed": len(preprocessed_data)
        }
    except Exception as e:
        logger.exception("Error during preprocessing.")
        return {"error": str(e)}

