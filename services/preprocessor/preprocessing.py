import os
import re
import sys
import json
import logging
import numpy as np
from pathlib import Path

# Base path dalam container
BASE_PATH = Path("app")

# Paths for storing preprocessing results (relatif terhadap /app)
SCRAPED_DATA_PATH = BASE_PATH.parent / "data" / "raw" / "mit_scraped_1000.json"
PREPROCESSED_DATA_PATH = BASE_PATH.parent / "data" / "processed" / "data_preprocessed.json"
MODEL_LOCAL_PATH = str(BASE_PATH.parent / "runs" / "local_models" / "all-MiniLM-L6-v2")
EMBEDDING_PATH = BASE_PATH.parent / "data" / "processed" / "embeddings.npy"
TFIDF_FEATURES_PATH = BASE_PATH.parent / "data" / "processed" / "tfidf_features.json"

# Ensure directories exist
os.makedirs(BASE_PATH.parent / "data" / "processed", exist_ok=True)

#Logging configuration
logging.basicConfig(
    level=logging.INFO,  # Tampilkan level INFO dan di atasnya
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Arahkan ke stdout
)

def clean_text(text):
    """ Cleans text by removing special characters, numbers, and stopwords, and applying lemmatization. """
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    import nltk

    try:
        # Ensure necessary NLTK resources are downloaded
        nltk.download("punkt_tab", quiet=True)
        nltk.download("stopwords", quiet=True)
        nltk.download("wordnet", quiet=True)

        stopwords_en = set(stopwords.words("english"))
        lemmatizer = WordNetLemmatizer()

        text = text.lower().strip()
        text = re.sub(r"\d+", "", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        tokens = word_tokenize(text)
        tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stopwords_en]
        return " ".join(tokens)
    except Exception as e:
        logging.error(f"Error in clean_text: {e}")
        return ""

def preprocess_papers(papers, output_path=PREPROCESSED_DATA_PATH):
    """Cleans all text fields in the dataset, including list-of-strings fields like authors."""
    seen = set()
    cleaned_papers = []

    for paper in papers:
        cleaned_paper = {}
        for key, value in paper.items():
            if isinstance(value, str):
                cleaned_paper[key] = clean_text(value)
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                combined = " ".join(value)
                cleaned_paper[key] = clean_text(combined)
            else:
                cleaned_paper[key] = value

        # Buat kunci unik dari nilai-nilainya
        paper_key = tuple(tuple(v) if isinstance(v, list) else v for v in cleaned_paper.values())
        if paper_key not in seen:
            seen.add(paper_key)
            cleaned_papers.append(cleaned_paper)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_papers, f, indent=2, ensure_ascii=False)
        logging.info(f"Preprocessing completed! {len(cleaned_papers)} unique records saved in '{output_path}'")
    except Exception as e:
        logging.error(f"Error saving preprocessed data: {e}")

    return cleaned_papers

def compute_embeddings(texts, save_path=EMBEDDING_PATH):
    """Compute and save embeddings if not already saved."""
    from sentence_transformers import SentenceTransformer

    logging.info("Computing embeddings using SentenceTransformer.")
    try:
        if os.path.exists(MODEL_LOCAL_PATH):
            model = SentenceTransformer(MODEL_LOCAL_PATH)
        else:
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            model.save(MODEL_LOCAL_PATH)
        embeddings = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
        np.save(save_path, embeddings)
        logging.info(f"Embeddings saved at {save_path}")
        return embeddings
    except Exception as e:
        logging.error(f"Error in compute_embeddings: {e}")
        return None

def compute_tfidf(texts, feature_path=TFIDF_FEATURES_PATH):
    """Compute and save TF-IDF representation of the texts."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(texts)
        with open(feature_path, "w", encoding="utf-8") as f:
            json.dump(vectorizer.get_feature_names_out().tolist(), f, indent=2)
        logging.info(f"TF-IDF features saved at {feature_path}")
        return tfidf_matrix
    except Exception as e:
        logging.error(f"Error in compute_tfidf: {e}")
        return None