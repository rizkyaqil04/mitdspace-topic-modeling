from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter()

PREPROCESSED_DATA_PATH = Path("data/processed/data_preprocessed.json")

@router.get("/preprocessed")
async def get_preprocessed_data():
    """
    Mengembalikan hasil preprocessing dalam bentuk JSON.
    """
    if PREPROCESSED_DATA_PATH.exists():
        with open(PREPROCESSED_DATA_PATH, "r") as f:
            data = json.load(f)
        return {"preprocessed_data": data}
    else:
        return {"error": "Preprocessed data not found"}
