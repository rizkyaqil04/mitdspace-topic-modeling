import os
import json
import random
import logging
import numpy as np
from pathlib import Path

# Paths for storing preprocessing results
PAPERS_DATA_PATH = Path("data/processed/data_preprocessed.json")
MODEL_LOCAL_PATH = "models/all-MiniLM-L6-v2"
MODEL_PATH = "models/bertopic_model"
EMBEDDING_PATH = "data/processed/embeddings.npy"
TOPICS_PATH = "results/topics.json"
LOG_PATH = "logs/training.log"

# Ensure directories exist
os.makedirs("data/processed", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure the seed
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

def compute_embeddings(texts, save_path=EMBEDDING_PATH):
    """ Compute embeddings from texts using SentenceTransformer """
    from sentence_transformers import SentenceTransformer
    
    logging.info("Computing embeddings using SentenceTransformer.")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts)
    np.save(save_path, embeddings)
    logging.info(f"Embeddings saved at {save_path}")
    return embeddings

def compute_topics_with_bertopic(papers, save_model=True):
    """ Train BERTopic using HDBSCAN and c-TFIDF """
    from sentence_transformers import SentenceTransformer
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    
    texts = [paper["title"] for paper in papers]
    
    logging.info("Computing embeddings using SentenceTransformer.")

    if os.path.exists(MODEL_LOCAL_PATH):
        model = SentenceTransformer(MODEL_LOCAL_PATH)  # Gunakan model dari lokal
    else:
        model = SentenceTransformer("all-MiniLM-L6-v2")  # Unduh dari Hugging Face
        model.save(MODEL_LOCAL_PATH)  # Simpan untuk penggunaan selanjutnya
    
    # model = SentenceTransformer("all-MiniLM-L6-v2")
    
    embeddings = model.encode(texts)
    
    retrain = True

    if retrain:
        logging.info("Training a new BERTopic model.")
        umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=SEED)
        hdbscan_model = HDBSCAN(min_cluster_size=5, metric="euclidean", cluster_selection_method="eom", prediction_data=True)

        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=None,
            embedding_model=model
        )
        
        topic_model.fit_transform(texts, embeddings)

        if save_model:
            topic_model.save(MODEL_PATH)
            logging.info(f"Model saved at {MODEL_PATH}")
    else:
        logging.info("Loading existing BERTopic model.")
        topic_model = BERTopic.load(MODEL_PATH)

    topics, _ = topic_model.transform(texts)
    return topic_model, [int(t) for t in topics]

if __name__ == "__main__":
    if not PAPERS_DATA_PATH.exists():
        logging.error(f"File {PAPERS_DATA_PATH} not found!")
        raise FileNotFoundError(f"File {PAPERS_DATA_PATH} not found!")
    
    logging.info("Loading data from JSON file.")
    papers = json.loads(PAPERS_DATA_PATH.read_text(encoding="utf-8"))
    topic_model, topics = compute_topics_with_bertopic(papers)

    # Displaying topic count
    topic_info = topic_model.get_topic_info()
    num_topics = len(topic_info)
    
    logging.info(f"Total Topics Found: {num_topics}")
    
    # Save topic list to a file
    with open(TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(topic_info.to_dict(orient="records"), f, indent=4)
    
    logging.info(f"Topics saved to {TOPICS_PATH}")
