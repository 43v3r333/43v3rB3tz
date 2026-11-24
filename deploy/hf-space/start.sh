#!/bin/sh
# Starts the whole 43v3rB3tz backend inside one Hugging Face Space container.
set -e

for v in DATABASE_URL DATABASE_URL_SYNC SECRET_KEY S3_ENDPOINT S3_ACCESS_KEY S3_SECRET_KEY S3_BUCKET OPS_TOKEN; do
  eval "val=\${$v:-}"
  if [ -z "$val" ]; then echo "Missing Space secret: $v" >&2; MISSING=1; fi
done
[ -n "${MISSING:-}" ] && { echo "Add the missing secrets in the Space settings, then restart." >&2; exit 1; }

export PROMETHEUS_MULTIPROC_DIR="$(mktemp -d /tmp/prophitbet-metrics.XXXXXX)"

redis-server --daemonize yes --dir /tmp --save "" --appendonly no --maxmemory 256mb
if command -v qdrant >/dev/null 2>&1; then
  mkdir -p /tmp/qdrant
  QDRANT__STORAGE__STORAGE_PATH=/tmp/qdrant QDRANT__SERVICE__HOST=127.0.0.1 qdrant >/tmp/qdrant.log 2>&1 &
fi

cd /app/backend && alembic upgrade head && cd /app

# Both queues in one worker (the PC ran two), plus the beat scheduler (fixtures every 6 h,
# league sync 06:00, predictions 07:00, results), all at concurrency 1 to stay inside 16 GB.
celery -A backend.app.workers.celery_app worker --loglevel=info --concurrency=1 -Q celery,data_sync &
celery -A backend.app.workers.celery_app beat --loglevel=info --schedule /tmp/celerybeat-schedule &

exec uvicorn backend.app.main:app --host 0.0.0.0 --port 7860 --workers 1 --proxy-headers --forwarded-allow-ips='*'
