# Gunakan base image Python
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy file proyek ke dalam container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-dev.txt

RUN playwright install --with-deps chromium

# Expose port untuk API
EXPOSE 8000

# Jalankan aplikasi FastAPI
CMD ["uvicorn", "run_api:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
