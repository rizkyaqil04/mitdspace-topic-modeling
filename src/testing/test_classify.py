import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from bertopic import BERTopic

# Paths
DATA_PATH = Path("data/processed/scholar_preprocessed.json")
MODEL_PATH = "models/bertopic_model"
RESULT_PATH = "results/output_testing.csv"
LOG_FILE_PATH = "logs/testing.log"


# Ensure directories exist
os.makedirs("results", exist_ok=True)
os.makedirs("logs", exist_ok=True)


# Configure logging
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load the existing model
def load_model():
    """ Load the pre-trained BERTopic model """
    if not os.path.exists(MODEL_PATH):
        logging.error(f"Model not found at {MODEL_PATH}. Please train the model first!")
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Please train the model first!")
    
    logging.info("Loading BERTopic model...")
    return BERTopic.load(MODEL_PATH)

# Classify new data
def classify_new_texts(model, new_texts):
    """ Classify new texts into existing topics """
    logging.info("Classifying new texts...")
    
    topics, _ = model.transform(new_texts)
    topic_info = model.get_topic_info()
    topic_labels = {row["Topic"]: f"{row['Name']}" for _, row in topic_info.iterrows()}
    
    results = []
    
    for text, topic in zip(new_texts, topics):
        topic_label = topic_labels.get(topic, "No Topic")
        results.append({"Text": text, "Topic": topic, "Label": topic_label})
    
    df = pd.DataFrame(results)
    df.to_csv(RESULT_PATH, index=False)
    
    logging.info(f"Classification completed. Results saved to '{output_file}'")
    
if __name__ == "__main__":
    if not DATA_PATH.exists():
        logging.error(f"Data file '{DATA_PATH}' not found!")
    else:
        try:
            papers = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            texts = [paper["title"] for paper in papers]
            logging.info(f"Loaded {len(texts)} texts from '{DATA_PATH}'")
            
            model = load_model()
            classify_new_texts(model, texts)
        except Exception as e:
            logging.error(f"Error processing the data: {e}")
