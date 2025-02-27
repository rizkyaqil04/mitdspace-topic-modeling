import asyncio
import json
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define paths
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = Path("results")
MODELS_DIR = Path("models")

# SCRAPED_FILE = RAW_DIR / "mit_scraped.json"
PREPROCESSED_FILE = PROCESSED_DIR / "data_preprocessed.json"
CLUSTERING_FILE = RESULTS_DIR / "topics.json"
MODEL_PATH = MODELS_DIR / "bertopic_model"

async def main():
    # print(f"Using data from {SCRAPED_FILE}")

    from src.preprocessing.preprocessing import preprocess_papers
    from src.training.bert import compute_topics_with_bertopic

    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # ===============================================================================================
    # 🔍 Checking for existing scraped data
    async def scrape_data():
        logging.info("🚀 Choose scraping source:")
        print("1. Sinta\n2. Scholar\n3. MIT")
        choice = input("Enter choice (1/2/3): ").strip()
        
        if choice == "1":
            from src.scraping.sinta_scraping import scraping_data as sinta_scraping
            query = input("Enter search query: ").strip()
            max_pages = int(input("Enter max pages: "))
            return await sinta_scraping(query, max_pages)
        elif choice == "2":
            from src.scraping.scholar_scraping import scraping_data as scholar_scraping
            max_pages = int(input("Enter max pages: "))
            return await scholar_scraping(max_pages)
        elif choice == "3":
            from src.scraping.mit_scraping import scraping_data as mit_scraping
            title_per_page = int(input("Enter titles per page: "))
            max_pages = int(input("Enter max pages: "))
            return await mit_scraping(title_per_page, max_pages)
        else:
            logging.error("❌ Invalid choice. Exiting.")
            return None
    
    if any(RAW_DIR.glob("*.json")):
        logging.info("✅ Scraped data found!")
        rescrape = input("🔄 Rescrape data? (y/n): ").strip().lower()
        if rescrape == "y":
            papers = await scrape_data()
        else:
            logging.info("➡ Available scraped files in 'data/raw':")
            files = list(RAW_DIR.glob("*.json"))
            if not files:
                logging.error("❌ No existing scraped files found!")
                return
            
            for idx, file in enumerate(files, 1):
                print(f"{idx}. {file.name}")
            file_choice = int(input("Select a file number: ")) - 1
            if 0 <= file_choice < len(files):
                SCRAPED_FILE = files[file_choice]
                papers = json.loads(SCRAPED_FILE.read_text(encoding="utf-8"))
            else:
                logging.error("❌ Invalid selection. Exiting.")
                return
    else:
        logging.info("❌ Scraped data not found! Scraping now...")
        papers = await scrape_data()
    
    logging.info("✅ Scraping complete!")

    # ===============================================================================================
    # 🔍 Checking for existing preprocessed data
    if PREPROCESSED_FILE.exists():
        logging.info("✅ Preprocessed data found!")
        reprocess = input("🔄 Reprocess data? (y/n): ").strip().lower()
        if reprocess == "y":
            logging.info("🚀 Reprocessing...")
            cleaned_papers = preprocess_papers(papers)
            PREPROCESSED_FILE.write_text(json.dumps(cleaned_papers, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            logging.info("➡ Using existing preprocessed data.")
            cleaned_papers = json.loads(PREPROCESSED_FILE.read_text(encoding="utf-8"))
    else:
        logging.info("❌ Preprocessed data not found! Preprocessing now...")
        cleaned_papers = preprocess_papers(papers)
        PREPROCESSED_FILE.write_text(json.dumps(cleaned_papers, indent=2, ensure_ascii=False), encoding="utf-8")

    logging.info("✅ Preprocessing complete!")

    # ===============================================================================================
    # 🔍 Validating preprocessed data before clustering
    if not cleaned_papers:
        logging.error("❌ No valid preprocessed data found! Stopping process.")
        return

    logging.info("🔄 Running BERTopic for clustering...")
    try:
        topic_model, topics = compute_topics_with_bertopic(cleaned_papers)
        topic_info = topic_model.get_topic_info()
    except Exception as e:
        logging.error(f"❌ Error in BERTopic processing: {e}")
        return

    results = {"clusters": topics, "topic_info": topic_info.to_dict(orient="records")}
    # CLUSTERING_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    logging.info(f"✅ Clustering complete! Results saved to '{CLUSTERING_FILE}'")

    # ===============================================================================================
    # 🔍 Displaying topic count and list
    num_topics = len(topic_info)
    topic_list = topic_info["Name"].tolist()

    print(f"\n📊 Total Topics Found: {num_topics}")
    print("📌 Topic List:")
    for idx, topic in enumerate(topic_list, start=1):
        print(f"  {idx}. {topic}")

if __name__ == "__main__":
    asyncio.run(main())
