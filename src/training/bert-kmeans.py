import os
import numpy as np
import logging
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from umap import UMAP
from sklearn.cluster import MiniBatchKMeans
from bertopic.vectorizers import OnlineCountVectorizer, ClassTfidfTransformer

# Paths for storing preprocessing results
MODEL_PATH = "models/bertopic_model"
EMBEDDING_PATH = "data/processed/embeddings.npy"
LLOG_PATH = "logs/training.log"
BATCH_SIZE = 1000  # Batch size for partial fitting

# Ensure directories exist
os.makedirs("data/processed", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("results", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Function to compute word embeddings
def compute_embeddings(texts, save_path=EMBEDDING_PATH):
    """ Compute embeddings from texts using SentenceTransformer """
    logging.info("Computing embeddings...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts)
    np.save(save_path, embeddings)
    logging.info(f"Embeddings saved at {save_path}")
    return embeddings

# Function to process topic modeling in batches
def compute_topics_with_bertopic(papers, save_model=True):
    """ Train BERTopic with MiniBatchKMeans and c-TFIDF using batch processing """
    logging.info("Starting topic modeling...")
    texts = [paper["title"] for paper in papers]

    # Load precomputed embeddings if available
    if os.path.exists(EMBEDDING_PATH):
        embeddings = np.load(EMBEDDING_PATH)
        logging.info("Loaded precomputed embeddings.")
    else:
        embeddings = compute_embeddings(texts)

    retrain = not os.path.exists(MODEL_PATH)

    if retrain:
        logging.info("Training a new BERTopic model...")

        # Prepare models
        umap_model = UMAP(n_components=5, random_state=0)
        cluster_model = MiniBatchKMeans(n_clusters=10, random_state=0, batch_size=BATCH_SIZE)
        vectorizer_model = OnlineCountVectorizer(stop_words="english", decay=0.01)
        ctfidf_model = ClassTfidfTransformer()

        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=cluster_model,
            vectorizer_model=vectorizer_model,
            ctfidf_model=ctfidf_model,
            embedding_model="all-MiniLM-L6-v2",
        )

        # Process in batches
        text_chunks = [texts[i:i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]
        embedding_chunks = [embeddings[i:i + BATCH_SIZE] for i in range(0, len(embeddings), BATCH_SIZE)]

        for batch_texts, batch_embeddings in zip(text_chunks, embedding_chunks):
            topic_model.partial_fit(batch_texts, batch_embeddings)

        # Save the trained model
        if save_model:
            topic_model.save(MODEL_PATH)
            logging.info(f"Model saved at {MODEL_PATH}")
    else:
        logging.info("Loading existing BERTopic model...")
        topic_model = BERTopic.load(MODEL_PATH)

    # Transform texts
    topics, _ = topic_model.transform(texts, embeddings)
    topics = [int(t) for t in topics]

    # Save topics to file
    topics_file = os.path.join(RESULTS_DIR, "topics")
    with open(topics_file, "w") as f:
        f.write("\n".join(map(str, topics)))
    logging.info(f"Topics saved at {topics_file}")

    return topic_model, topics
