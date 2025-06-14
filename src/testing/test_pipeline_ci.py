import json
import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))  # Tambahkan root project ke path

from services.preprocessor.preprocessing import clean_text, preprocess_papers
from services.trainer.bert import compute_topics_with_bertopic


def test_clean_text_basic():
    text = "This is a simple test sentence, with punctuation! And numbers 123."
    cleaned = clean_text(text)
    assert isinstance(cleaned, str)
    assert "test" in cleaned

def test_preprocessing_minimal_data(tmp_path):
    papers = [
        {"title": "Deep Learning for NLP", "authors": ["John Doe", "Jane Smith"]},
        {"title": "Quantum Computing Basics", "authors": ["Alice Bob"]},
    ]
    out_path = tmp_path / "preprocessed.json"
    cleaned = preprocess_papers(papers, output_path=out_path)
    assert isinstance(cleaned, list)
    assert len(cleaned) == 2
    assert out_path.exists()

def test_topic_modeling_runs():
    papers = [
        {"title": "deep learning for nlp", "authors": ["john doe"]},
        {"title": "transformers in computer vision", "authors": ["jane smith"]},
        {"title": "advances in reinforcement learning", "authors": ["alice"]},
        {"title": "quantum computing basics", "authors": ["bob"]},
        {"title": "graph neural networks overview", "authors": ["charlie"]},
        {"title": "large language models and reasoning", "authors": ["dave"]}
    ]
    model, topics = compute_topics_with_bertopic(papers)
    assert hasattr(model, "get_topic")
    assert isinstance(topics, list)
    assert len(topics) == len(papers)

