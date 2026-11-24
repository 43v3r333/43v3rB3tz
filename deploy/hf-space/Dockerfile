# 43v3rB3tz backend for a free Hugging Face Docker Space (CPU basic: 2 vCPU / 16 GB).
# One container runs everything the PC's docker-compose ran for the API:
#   Redis (queue) + Qdrant (MiroFish vectors) + Celery worker + Celery beat + FastAPI (port 7860).
# Postgres = Neon, model files = S3-compatible bucket (Backblaze B2), both set as Space secrets.
# Built and pushed by .github/workflows/deploy-hf-space.yml (build context = assembled Space repo).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev redis-server curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Qdrant single binary (state is ephemeral on the free tier; MiroFish rebuilds it).
ARG QDRANT_VERSION=v1.15.4
RUN curl -fsSL "https://github.com/qdrant/qdrant/releases/download/${QDRANT_VERSION}/qdrant-x86_64-unknown-linux-musl.tar.gz" \
        | tar -xz -C /usr/local/bin qdrant || echo "Qdrant download failed; MiroFish vectors disabled"

# Spaces run as uid 1000.
RUN useradd -m -u 1000 user
WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY src/ /app/src/
COPY storage/network/ /app/storage/network/
COPY backend/ /app/backend/
COPY start.sh /app/start.sh
COPY aws_config /home/user/.aws/config
RUN chmod +x /app/start.sh && chown -R user:user /app /home/user

USER user
ENV HOME=/home/user \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ML_CORE_PATH=/app/src \
    REDIS_URL=redis://127.0.0.1:6379/0 \
    QDRANT_HOST=127.0.0.1 \
    QDRANT_PORT=6333 \
    QDRANT_URL=http://127.0.0.1:6333 \
    AWS_CONFIG_FILE=/home/user/.aws/config

EXPOSE 7860
CMD ["/app/start.sh"]
