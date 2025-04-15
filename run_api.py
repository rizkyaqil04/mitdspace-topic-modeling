import uvicorn
from fastapi import FastAPI
<<<<<<< HEAD
from src.api.scrape_svc import app as scraping_app
from src.api.menampilkan_svc import app as menampilkan_app

app = FastAPI()

# Menyertakan sub-app untuk scraping dan preprocessing
app.mount("/a", scraping_app)
app.mount("/b", menampilkan_app)
=======
from src.api.scrape_svc import router as scraping_router
from src.api.preprocessing_svc import router as preprocessing_router
from src.api.menampilkan_svc import router as menampilkan_router
from src.api.training_svc import router as training_router

app = FastAPI()

# Sertakan router tanpa prefix
app.include_router(scraping_router, tags=["Scraping"])
app.include_router(preprocessing_router, tags=["Preprocessing"])
app.include_router(menampilkan_router, tags=["Menampilkan"])
app.include_router(training_router, tags=["Training"])
>>>>>>> Aqill's

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
