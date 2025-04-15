import os
import re
import json
import logging
import numpy as np
from pathlib import Path
from src.utils.logger import setup_logger

# Paths for storing preprocessing results
SCRAPED_DATA_PATH = Path("data/raw/mit_scraped_10k.json")
PREPROCESSED_DATA_PATH = Path("data/processed/data_preprocessed.json")
MODEL_LOCAL_PATH = "models/all-MiniLM-L6-v2"
EMBEDDING_PATH = Path("data/processed/embeddings.npy")
TFIDF_FEATURES_PATH = Path("data/processed/tfidf_features.json")

# Ensure directories exist
os.makedirs("data/processed", exist_ok=True)

# Configure Logging
logger = setup_logger("preprocessing")

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

        text = text.lower().strip()  # Convert to lowercase & remove leading/trailing spaces
        text = re.sub(r"\d+", "", text)  # Remove numbers
        text = re.sub(r"\s+", " ", text)  # Remove excessive spaces
        text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
        tokens = word_tokenize(text)  # Tokenization
        tokens = [lemmatizer.lemmatize(word) for word in tokens]  # Lemmatization
        tokens = [word for word in tokens if word not in stopwords_en]  # Remove stopwords

        return " ".join(tokens)
    except Exception as e:
        logging.error(f"Error in clean_text: {e}")
        return ""

def preprocess_papers(papers, output_path=PREPROCESSED_DATA_PATH):
    """Cleans all text fields in the dataset without relying on specific column names."""
    seen = set()
    cleaned_papers = []

    try:
        for paper in papers:
            cleaned_paper = {}

            # Clean for every items in data
            for key, value in paper.items():
                if isinstance(value, str):  # Only item that has texts in it
                    cleaned_paper[key] = clean_text(value)
                else:
                    cleaned_paper[key] = value  # If its not, then ignore it

            # Using tuple to check any duplicate
            paper_key = tuple(cleaned_paper.values())

            if paper_key not in seen:
                seen.add(paper_key)
                cleaned_papers.append(cleaned_paper)

        # Save preprocessing results to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_papers, f, indent=2, ensure_ascii=False)

        logging.info(f"Preprocessing completed! {len(cleaned_papers)} unique records saved in '{output_path}'")
        return cleaned_papers
    except Exception as e:
        logging.error(f"Error in preprocess_papers: {e}")
        return []


def compute_embeddings(texts, save_path=EMBEDDING_PATH):
    """Compute and save embeddings if not already saved."""
    from sentence_transformers import SentenceTransformer

    # if Path(save_path).exists():
    #     logging.info(f"Loading existing embeddings from {save_path}")
    #     return np.load(save_path)
    
    logging.info("Computing embeddings using SentenceTransformer.")
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    if os.path.exists(MODEL_LOCAL_PATH):
        model = SentenceTransformer(MODEL_LOCAL_PATH)  # Gunakan model dari lokal
    else:
        model = SentenceTransformer("all-MiniLM-L6-v2")  # Unduh dari Hugging Face
        model.save(MODEL_LOCAL_PATH)  # Simpan untuk penggunaan selanjutnya
    
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    np.save(save_path, embeddings)
    logging.info(f"Embeddings saved at {save_path}")
    
    return embeddings

def compute_tfidf(texts, feature_path=TFIDF_FEATURES_PATH):
    """Compute and save TF-IDF representation of the texts."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)  # Batasi fitur untuk efisiensi
        tfidf_matrix = vectorizer.fit_transform(texts)

        # Save extracted features to json file
        with open(feature_path, "w", encoding="utf-8") as f:
            json.dump(vectorizer.get_feature_names_out().tolist(), f, indent=2)

        logging.info(f"TF-IDF features saved at {feature_path}")
        return tfidf_matrix
    except Exception as e:
        logging.error(f"Error in compute_tfidf: {e}")
        return None

if __name__ == "__main__":
    if not SCRAPED_DATA_PATH.exists():
        logging.warning(f"File '{SCRAPED_DATA_PATH}' not found. Run 'scraping.py' first.")
    else:
        try:
            # Preprocessing and Cleaning Data
            papers = json.loads(SCRAPED_DATA_PATH.read_text(encoding="utf-8"))
            logging.info(f"Loaded {len(papers)} records from '{SCRAPED_DATA_PATH}'")
            processed_papers = preprocess_papers(papers)
            
            # Features Extraction
            texts = [paper["title"] for paper in processed_papers]
            compute_embeddings(texts)
            compute_tfidf(texts)

        except Exception as e:
            logging.error(f"Error reading JSON file: {e}")
