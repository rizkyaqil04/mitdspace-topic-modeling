import uvicorn
from fastapi import FastAPI
from src.api.scrape_svc import router as scraping_router
from src.api.preprocessing_svc import router as preprocessing_router
from src.api.menampilkan_svc import router as menampilkan_router
from src.api.training_svc import router as training_router
from src.api.monitor_svc import router as monitoring_router

app = FastAPI()

# Sertakan router tanpa prefix
app.include_router(scraping_router, tags=["Scraping"])
app.include_router(preprocessing_router, tags=["Preprocessing"])
app.include_router(menampilkan_router, tags=["Menampilkan"])
app.include_router(training_router, tags=["Training"])
app.include_router(monitoring_router, tags=["Monitoring"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
