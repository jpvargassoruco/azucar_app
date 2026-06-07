FROM python:3.12-slim

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Supercronic (cron runner for Docker)
COPY supercronic /usr/local/bin/supercronic
RUN chmod +x /usr/local/bin/supercronic

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start supercronic with the loaded crontab file
CMD ["supercronic", "crontab"]
