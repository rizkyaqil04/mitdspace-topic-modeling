from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import logging
import numpy as np

from src.training.bert import compute_topics_with_bertopic, compute_coherence_score
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("training_svc")

# Path to the preprocessed data
PAPERS_DATA_PATH = Path("data/processed/data_preprocessed.json")
EMBEDDING_PATH = Path("data/processed/embeddings.npy")
TOPICS_PATH = Path("results/topics.json")

@router.post("/train")
def train_topic_model():
    """
    Melakukan training menggunakan BERTopic.
    """

    try:
        # Load preprocessed data
        if not PAPERS_DATA_PATH.exists():
            logger.error(f"File {PAPERS_DATA_PATH} not found.")
            return {"error": "Preprocessed data not found."}

        if not EMBEDDING_PATH.exists():
            logger.error(f"File {EMBEDDING_PATH} not found.")
            return {"error": "Embeddings file not found. Please run preprocessing first."}

        logger.info("Loading preprocessed papers...")
        papers = json.loads(PAPERS_DATA_PATH.read_text(encoding="utf-8"))
        titles = [paper["title"] for paper in papers]
        logger.info(f"Loaded {len(papers)} papers for training.")

        logger.info("Training BERTopic model...")
        topic_model, topics = compute_topics_with_bertopic(papers)
        logger.info("BERTopic model trained.")

        tokenized_titles = [title.split() for title in titles]

        logger.info("Computing coherence score...")
        coherence_score = compute_coherence_score(topic_model, tokenized_titles)
        logger.info(f"Coherence Score: {coherence_score:.4f}")

        topic_info = topic_model.get_topic_info()
        logger.info(f"Training done. {len(topic_info)} topics found.")

        # Simpan hasil topik ke file
        logger.info(f"Saving topic information to {TOPICS_PATH}")

        TOPICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOPICS_PATH, "w", encoding="utf-8") as f:
            json.dump(topic_info.to_dict(orient="records"), f, indent=4)

        logger.info("Topic information saved.")

        return {
            "message": "Training completed successfully.",
            "num_topics": len(topic_info),
            "coherence_score": coherence_score,
            "example_topics": topic_info.head(5).to_dict(orient="records")
        }

    except Exception as e:
        logger.exception("Error during training.")
        
        return {"error": str(e)}

    