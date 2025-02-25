import os
import re
import json
import logging
from pathlib import Path

# Paths for storing preprocessing results
SCRAPED_DATA_PATH = Path("data/raw/mit_scraped.json")
PREPROCESSED_DATA_PATH = "data/processed/data_preprocessed.json"
LOG_FILE_PATH = "logs/preprocessing.log"

# Ensure directories exist
os.makedirs("data/processed", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def clean_text(text):
    """ Cleans text by removing special characters, numbers, and stopwords, and applying lemmatization. """
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    import nltk

    try:
        # Ensure necessary NLTK resources are downloaded
        nltk.download("punkt", quiet=True)
        nltk.download("stopwords", quiet=True)
        nltk.download("wordnet", quiet=True)

        # Initialize stopwords and lemmatizer
        # stopword_factory = StopWordRemoverFactory()
        # stopwords_id = set(stopword_factory.get_stop_words())
        stopwords_en = set(stopwords.words("english"))
        lemmatizer = WordNetLemmatizer()

        text = text.lower().strip()  # Convert to lowercase & remove leading/trailing spaces
        text = re.sub(r"\d+", "", text)  # Remove numbers
        text = re.sub(r"\s+", " ", text)  # Remove excessive spaces
        text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
        tokens = word_tokenize(text)  # Tokenization
        tokens = [lemmatizer.lemmatize(word) for word in tokens]  # Lemmatization
        # tokens = [word for word in tokens if word not in stopwords_id and word not in stopwords_en]  # Remove stopwords
        tokens = [word for word in tokens if word not in stopwords_en]  # Remove stopwords

        return " ".join(tokens)
    except Exception as e:
        logging.error(f"Error in clean_text: {e}")
        return ""

def preprocess_papers(papers, output_path=PREPROCESSED_DATA_PATH):
    """ Cleans all text in scraped data, removes duplicates, and saves to a file. """
    seen = set()
    cleaned_papers = []

    try:
        for paper in papers:
            title = clean_text(paper.get("title", ""))
            description = clean_text(paper.get("description", ""))

            # Create a unique tuple based on title and description
            paper_key = (title, description)

            if paper_key not in seen:
                seen.add(paper_key)
                cleaned_papers.append({"title": title, "description": description})

        # Save preprocessing results to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_papers, f, indent=2, ensure_ascii=False)

        logging.info(f"Preprocessing completed! {len(cleaned_papers)} unique records saved in '{output_path}'")
        return cleaned_papers
    except Exception as e:
        logging.error(f"Error in preprocess_papers: {e}")
        return []

if __name__ == "__main__":
    if not SCRAPED_DATA_PATH.exists():
        logging.warning(f"File '{SCRAPED_DATA_PATH}' not found. Run 'scraping.py' first.")
    else:
        try:
            papers = json.loads(SCRAPED_DATA_PATH.read_text(encoding="utf-8"))
            logging.info(f"Loaded {len(papers)} records from '{SCRAPED_DATA_PATH}'")
            preprocess_papers(papers)
        except Exception as e:
            logging.error(f"Error reading JSON file: {e}")

#     # Cek apakah file hasil scraping tersedia
#     if not os.path.exists(SCRAPED_DATA_PATH):
#         print(f"⚠️  File '{SCRAPED_DATA_PATH}' tidak ditemukan. Jalankan 'scraping.py' terlebih dahulu.")
#     else:
#         # Load data dari file hasil scraping
#         with open(SCRAPED_DATA_PATH, "r", encoding="utf-8") as f:
#             papers = json.load(f)
#
#         # Preprocess data dan hapus duplikat
#         cleaned_papers = preprocess_papers(papers)
#
#         # Simpan hasil preprocessing ke file baru
#         with open(PREPROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
#             json.dump(cleaned_papers, f, indent=2, ensure_ascii=False)
#
#         print(f"✅ Preprocessing selesai! {len(cleaned_papers)} data unik disimpan dalam '{PREPROCESSED_DATA_PATH}'")
#
