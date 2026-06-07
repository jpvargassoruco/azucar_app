FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies required for compilation (e.g. pg config, cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --- Target for production API server ---
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- Target for background task worker ---
FROM base AS worker
CMD ["python", "-m", "app.workers.notification_worker"]
