# Gunakan base image Python
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy file proyek ke dalam container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
<<<<<<< HEAD
    && pip install --no-cache-dir -r requirements.txt
=======
    && pip install --no-cache-dir -r requirements-dev.txt
>>>>>>> Aqill's

RUN playwright install --with-deps chromium

# Expose port untuk API
EXPOSE 8000

# Jalankan aplikasi FastAPI
<<<<<<< HEAD
CMD ["uvicorn", "run_api:app", "--host", "0.0.0.0", "--port", "8000"]
=======
CMD ["uvicorn", "run_api:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
>>>>>>> Aqill's
