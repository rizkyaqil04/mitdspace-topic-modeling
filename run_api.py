import uvicorn
from fastapi import FastAPI
from src.api.scrape_svc import app as scraping_app
from src.api.menampilkan_svc import app as menampilkan_app

app = FastAPI()

# Menyertakan sub-app untuk scraping dan preprocessing
app.mount("/a", scraping_app)
app.mount("/b", menampilkan_app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
