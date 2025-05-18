import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json
import random
import logging
import numpy as np
import mlflow
from pathlib import Path
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora.dictionary import Dictionary
from src.utils.logger import setup_logger
from prometheus_client import start_http_server, Summary, Gauge
import time

start_http_server(8001)

# Definisikan metrik Prometheus
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

# Paths for storing preprocessing results
PAPERS_DATA_PATH = Path("data/processed/data_preprocessed.json")
MODEL_LOCAL_PATH = "models/all-MiniLM-L6-v2"
MODEL_PATH = "models/bertopic_model"
EMBEDDING_PATH = "data/processed/embeddings.npy"
TOPICS_PATH = "results/topics.json"

# Ensure directories exist
os.makedirs("data/processed", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)

# Configure Logging
logger = setup_logger("training")

# Configure the seed
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

@training_duration.time()
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
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')  # Unduh dari Hugging Face
        model.save(MODEL_LOCAL_PATH)  # Simpan untuk penggunaan selanjutnya
    
    embeddings = np.load(EMBEDDING_PATH)
    
    retrain = True

    if retrain:
        n_neighbors = 4
        n_components = 5
        min_dist = 0.093
        min_cluster_size = 20

        logging.info(f"Training a new BERTopic model. with n_neighbors = {n_neighbors}, n_components = {n_components}, min_dist = {min_dist}, min_cluster_size = {min_cluster_size}")
        
        umap_model = UMAP(n_neighbors=n_neighbors, n_components=n_components, min_dist=min_dist, metric="cosine", random_state=SEED)
        hdbscan_model = HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean", cluster_selection_method="eom", prediction_data=True)

        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=None, # menggunakan c-TFIDF
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

def compute_coherence_score(topic_model, tokenized_texts, top_n=3):
    """Compute coherence score using preprocessed tokenized texts"""
    # Buat dictionary dan corpus dari teks tokenized
    dictionary = Dictionary(tokenized_texts)
    corpus = [dictionary.doc2bow(text) for text in tokenized_texts]

    # Ambil top-k kata dari setiap topik
    topic_words = []
    for topic_id in range(len(topic_model.get_topics())):
        topic = topic_model.get_topic(topic_id)
        if topic:  # hanya jika topik tidak kosong / bukan False
            words = [word for word, _ in topic[:top_n]]
            topic_words.append(words)


    coherence_model = CoherenceModel(
        topics=topic_words,
        texts=tokenized_texts,
        dictionary=dictionary,
        coherence='c_v'
    )

    return coherence_model.get_coherence()

if __name__ == "__main__":
    if not PAPERS_DATA_PATH.exists():
        logging.error(f"File {PAPERS_DATA_PATH} not found!")
        raise FileNotFoundError(f"File {PAPERS_DATA_PATH} not found!")

    logging.info("Loading data from JSON file.")
    papers = json.loads(PAPERS_DATA_PATH.read_text(encoding="utf-8"))
    
    mlflow.set_experiment("bertopic_experiment")

    # Tokenized texts from preprocessed file
    tokenized_titles = [paper["title"].split() for paper in papers]

    # Compute coherence score
    coherence = compute_coherence_score(topic_model, tokenized_titles)
    coherence_score_metric.set(coherence)
    logging.info(f"Coherence Score (c_v): {coherence:.4f}")

    # Displaying topic count
    topic_info = topic_model.get_topic_info()
    num_topics_metric.set(topic_info)
    num_topics = len(topic_info)
    
    logging.info(f"Total Topics Found: {num_topics}")
    
    # Save topic list to a file
    with open(TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(topic_info.to_dict(orient="records"), f, indent=4)
    
    logging.info(f"Topics saved to {TOPICS_PATH}")