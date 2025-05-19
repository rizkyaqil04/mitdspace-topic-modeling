from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from src.utils.logger import setup_logger 

router = APIRouter()
logger = setup_logger("monitoring_svc")

@router.get("/monitoring")
def metrics():
    """
    Endpoint untuk monitoring Prometheus
    """
    try:
        data = generate_latest(REGISTRY)
        logger.info("Data monitoring berhasil diperoleh")
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.exception("Gagal mendapatkan data monitoring")
        return {"error": str(e)}