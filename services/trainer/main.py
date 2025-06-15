from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from bert import compute_topics_with_bertopic, compute_coherence_score, PAPERS_DATA_PATH, run_id
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
import json, argparse
from pathlib import Path

app = FastAPI()

# Pastikan path absolut di dalam container
BASE_PATH = Path(__file__).parent.resolve()
RESULT_PATH = BASE_PATH.parent / "runs" / run_id / "train_result.json"

class TrainResponse(BaseModel):
    message: str

class TrainResult(BaseModel):
    message: str
    num_topics: int = 0
    coherence_score: float = 0.0

def train_job():
    try:
        # Tulis status running di awal
        RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULT_PATH.write_text(json.dumps({
            "status": "running",
            "message": "Training in progress...",
            "num_topics": 0,
            "coherence_score": 0.0
        }, indent=2))

        if not PAPERS_DATA_PATH.exists():
            result = {
                "status": "error",
                "message": f"File '{PAPERS_DATA_PATH}' not found.",
                "num_topics": 0,
                "coherence_score": 0.0
            }
        else:
            papers = json.loads(PAPERS_DATA_PATH.read_text(encoding="utf-8"))
            tokenized_titles = [paper["title"].split() for paper in papers]
            topic_model, topics = compute_topics_with_bertopic(papers)
            coherence = compute_coherence_score(topic_model, tokenized_titles)
            num_topics = len(topic_model.get_topic_info())
            result = {
                "status": "done",
                "message": f"Training complete. {num_topics} topics found. Coherence: {coherence:.4f}",
                "num_topics": num_topics,
                "coherence_score": coherence
            }
        RESULT_PATH.write_text(json.dumps(result, indent=2))
    except Exception as e:
        RESULT_PATH.write_text(json.dumps({
            "status": "error",
            "message": str(e),
            "num_topics": 0,
            "coherence_score": 0.0
        }, indent=2))

@app.post("/train", response_model=TrainResponse)
def train_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(train_job)
    return {"message": "Training started in background. Check /result for progress."}

@app.get("/result", response_model=TrainResult)
def get_result():
    if not RESULT_PATH.exists():
        return {"message": "No training result found. Please run /train first.", "num_topics": 0, "coherence_score": 0.0}
    try:
        data = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        # Tambahkan info status ke response
        if data.get("status") == "running":
            data["message"] = "Training is still running..."
        return data
    except Exception as e:
        return {"message": str(e), "num_topics": 0, "coherence_score": 0.0}

@app.get("/monitoring")
def prometheus_metrics():
    """
    Endpoint untuk Prometheus monitoring
    """
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

def main():
    parser = argparse.ArgumentParser(description="Train topic model using BERTopic")
    _ = parser.parse_args()

    if not PAPERS_DATA_PATH.exists():
        print(f"❌ File '{PAPERS_DATA_PATH}' tidak ditemukan.")
        return

    papers = json.loads(PAPERS_DATA_PATH.read_text(encoding="utf-8"))
    tokenized_titles = [paper["title"].split() for paper in papers]
    topic_model, _ = compute_topics_with_bertopic(papers)
    compute_coherence_score(topic_model, tokenized_titles)

if __name__ == "__main__":
    main()