FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

ENV APP_MODE=api

COPY src/models/ml /app/src/models/ml
COPY src/workers /app/src/workers
COPY src/database /app/src/database

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

COPY src/api /app/src/api

EXPOSE 8000

CMD ["/bin/bash", "-c", "if [ \"$APP_MODE\" = \"worker\" ]; then python -m src.workers.ml_worker; else /app/docker-entrypoint.sh; fi"]
  
