import os
import sys
import json
import random
import logging
import shutil
import numpy as np
from pathlib import Path
from datetime import datetime
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora.dictionary import Dictionary
from prometheus_client import Summary, Gauge

# Base path dalam container
BASE_PATH = Path("app")

# Generate unique run ID using timestamp
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")  # contoh: 20250614_172355

# Prometheus metrics
training_duration = Summary(
    'bertopic_training_duration_seconds', 
    'Time spent training the BERTopic model'
)
coherence_score_metric = Gauge(
    'bertopic_coherence_score', 
    'Coherence score of the BERTopic model'
)
num_topics_metric = Gauge(
    'bertopic_num_topics', 
    'Number of topics discovered by the BERTopic model'
)

# Paths (relatif terhadap /app)
PAPERS_DATA_PATH = BASE_PATH.parent / "data" / "processed" / "data_preprocessed.json"
MODEL_LOCAL_PATH = str(BASE_PATH.parent / "runs" / "local_models" / "all-MiniLM-L6-v2")
SYMLINK_PATH = BASE_PATH.parent / "runs" / "topic_model"
RUN_DIR = BASE_PATH.parent / "runs" / run_id
MODEL_PATH = RUN_DIR / "bertopic_model"
EMBEDDING_PATH = RUN_DIR / "embeddings.npy"
TOPICS_PATH = RUN_DIR / "topics.json"

# Hapus jika sudah ada
if SYMLINK_PATH.exists() or SYMLINK_PATH.is_symlink():
    if SYMLINK_PATH.is_symlink() or SYMLINK_PATH.is_file():
        SYMLINK_PATH.unlink()
    else:
        shutil.rmtree(SYMLINK_PATH)

# Buat symlink ke model dinamis
os.symlink(MODEL_PATH.resolve(), SYMLINK_PATH)

# Ensure directories exist
for p in [PAPERS_DATA_PATH.parent, Path(MODEL_LOCAL_PATH).parent, Path(RUN_DIR), Path(MODEL_PATH).parent, TOPICS_PATH.parent]:
    os.makedirs(p, exist_ok=True)

#Logging configuration
logging.basicConfig(
    level=logging.INFO,  # Tampilkan level INFO dan di atasnya
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Arahkan ke stdout
)

# Seed
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

@training_duration.time()
def compute_topics_with_bertopic(papers, save_model=True):
    """Train BERTopic using HDBSCAN and c-TFIDF."""
    from sentence_transformers import SentenceTransformer
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN

    texts = [paper["title"] for paper in papers]
    logging.info("Computing embeddings using SentenceTransformer.")

    if os.path.exists(MODEL_LOCAL_PATH):
        model = SentenceTransformer(MODEL_LOCAL_PATH)
    else:
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        model.save(MODEL_LOCAL_PATH)

    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    np.save(EMBEDDING_PATH, embeddings)
    logging.info(f"Embeddings saved at {EMBEDDING_PATH}")

    logging.info("Training BERTopic model...")
    umap_model = UMAP(
        n_neighbors=4, n_components=5, min_dist=0.093, metric="cosine", random_state=SEED
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=5, metric="euclidean", cluster_selection_method="eom", prediction_data=True
    )

    topic_model = BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=None,
        embedding_model=model
    )
    topic_model.fit_transform(texts, embeddings)
    num_topics = len(topic_model.get_topic_info())
    num_topics_metric.set(num_topics)
    logging.info(f"Model trained. {num_topics} topics found.")

    if save_model:
        topic_model.save(MODEL_PATH)
        logging.info(f"Model saved at {MODEL_PATH}")

    # Save topics info
    topic_info = topic_model.get_topic_info()
    with open(TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(topic_info.to_dict(orient="records"), f, indent=4)
    logging.info(f"Topics saved to {TOPICS_PATH}")

    # MLflow logging (optional, non-blocking)
    try:
        import mlflow
        mlflow.set_experiment("bertopic_experiment")
        mlflow.log_metric("num_topics", num_topics)
        mlflow.log_artifact(str(TOPICS_PATH))
        mlflow.log_artifact(MODEL_PATH)
    except Exception as e:
        logging.warning(f"MLflow logging skipped: {e}")

    return topic_model, [int(t) for t in topic_model.topics_]

def compute_coherence_score(topic_model, tokenized_texts, top_n=3):
    """Compute coherence score using preprocessed tokenized texts."""
    dictionary = Dictionary(tokenized_texts)

    topic_words = []
    for topic_id in range(len(topic_model.get_topics())):
        topic = topic_model.get_topic(topic_id)
        if topic:
            words = [word for word, _ in topic[:top_n]]
            topic_words.append(words)

    coherence_model = CoherenceModel(
        topics=topic_words,
        texts=tokenized_texts,
        dictionary=dictionary,
        coherence='c_v'
    )
    score = coherence_model.get_coherence()
    coherence_score_metric.set(score)
    logging.info(f"{len(topic_words)} topics found")
    logging.info(f"Coherence Score (c_v): {score:.4f}")

    # MLflow logging (optional)
    try:
        import mlflow
        mlflow.log_metric("coherence_score", score)
    except Exception as e:
        logging.warning(f"MLflow logging skipped: {e}")

    return score
