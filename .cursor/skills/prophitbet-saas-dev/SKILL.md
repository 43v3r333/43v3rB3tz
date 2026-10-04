---
name: prophitbet-saas-dev
description: Run and operate the ProphitBet SaaS stack locally with Docker (compose, seed, admin pipeline).
---

# ProphitBet SaaS — local dev playbook

Use when starting the stack, seeding data, or running the admin prediction pipeline.

## Prerequisites

- Docker and Docker Compose
- Repo cloned; work from `prophitbet-saas/`

## Start services

```bash
cd prophitbet-saas
cp .env.example .env   # if .env missing; fill secrets as needed
docker compose up -d --build
```

Common URLs (host): API docs `http://localhost:8001/docs`, frontend `http://localhost:3001`, MinIO console `http://localhost:9001`.

## Seed database

```bash
docker compose exec backend python -m backend.seed
```

Creates admin user (see script output) and leagues from `storage/network/leagues.json` when missing.

## Admin pipeline (after sync completes)

Order matters:

1. **Sync League Data** — downloads/processes CSVs (long-running).
2. **Train House Models** — needs datasets per league.
3. **Scrape Fixtures** — FootyStats / fallback HTML.
4. **Generate Predictions** — inference + DB rows.

Trigger via Admin UI (logged-in admin) or POST `/admin/sync-leagues`, `/admin/train-house-models`, `/admin/scrape-fixtures`, `/admin/generate-predictions` with Bearer token.

## Restart workers after backend code changes

```bash
docker compose restart backend celery-worker
```

## Troubleshooting

- Empty predictions: confirm datasets exist, house models exist, fixtures scraped, then re-run generate task.
- CORS: ensure `FRONTEND_URL` / CORS in `backend/app/main.py` matches the Next dev URL.
