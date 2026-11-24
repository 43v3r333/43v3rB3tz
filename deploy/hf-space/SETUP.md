# 43v3rB3tz fully online (free): setup

Target: the FastAPI backend and Celery run in a **free Hugging Face Docker Space**, data lives in **Neon** (free),
and model files live in **Backblaze B2** (free 10 GB, key limited to one bucket). The PC is no longer needed.
Vercel keeps serving the frontend; only `INTERNAL_API_URL` changes.

Free-tier limits to know:
- The HF Space sleeps after 48 h with no requests. LifeOS checks it every 15 min, so it stays awake.
- A Space restart wipes Redis and Qdrant (the queue and MiroFish vectors). Those rebuild themselves; data and models are safe in Neon and B2.
- Neon free: about 0.5 GB of storage. Check your DB size in step 2 first.

## 1. Backblaze B2: model storage (Ethan, ~5 min)
1. Sign up at backblaze.com → B2 Cloud Storage (free tier).
2. Buckets → **Create bucket** `b3tz-models-<something-unique>`, **Private**.
3. Application Keys → **Add key** → allow access **only to that bucket**, Read and Write. Copy the **keyID** and **applicationKey** (shown once).
4. Note the bucket's **Endpoint** (e.g. `s3.us-west-004.backblazeb2.com`). The region is the middle part (`us-west-004`).

## 2. Move the database from the PC to Neon (Ethan, PowerShell, ~5 min)
Neon console → project **43v3rBetz** → Connect → copy the **direct** connection string (host **without** `-pooler`).
```powershell
cd C:\Users\p3rc\Desktop\dev\ProphitBet-Soccer-Bets-Predictor\prophitbet-saas
# size check (must be well under 500 MB)
docker compose exec -T postgres psql -U prophitbet -d prophitbet -c "select pg_size_pretty(pg_database_size('prophitbet'));"
# dump (schema + data) from the PC
docker compose exec -T postgres pg_dump -U prophitbet -d prophitbet --no-owner --no-acl > b3tz.sql
# load into Neon's public schema (paste your Neon string between the quotes)
docker run --rm -i -v "${PWD}:/d" postgres:18 psql "postgresql://USER:PASSWORD@HOST/neondb?sslmode=require" -v ON_ERROR_STOP=1 -f /d/b3tz.sql
```
Then delete `b3tz.sql`: it contains user data.

## 3. Hugging Face Space (Ethan, ~5 min)
1. Sign up at huggingface.co → **New Space** → name `43v3rb3tz-api`, SDK **Docker** → **Blank**, hardware **CPU basic (free)**, **Public** (the API has its own auth; private Spaces block Vercel).
2. Space → Settings → **Variables and secrets** → add these as **Secrets**:

| Secret | Value |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://USER:PASSWORD@HOST/neondb?ssl=require` (Neon direct host) |
| `DATABASE_URL_SYNC` | `postgresql://USER:PASSWORD@HOST/neondb?sslmode=require` |
| `S3_ENDPOINT` | `https://s3.<region>.backblazeb2.com` |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | B2 keyID / applicationKey |
| `S3_BUCKET` | your B2 bucket name |
| `AWS_DEFAULT_REGION` | the B2 region, e.g. `us-west-004` |
| `OPS_TOKEN` | same value as `OPS_TOKEN` in `prophitbet-saas/.env` on the PC |
| `SECRET_KEY` | same as in the PC `.env` (keeps users logged in) |
| everything else in the PC `.env` | e.g. Stripe and API-Football keys, **except** DATABASE_*, REDIS_*, S3_*, QDRANT_* |

3. Profile → Settings → **Access Tokens** → New token, type **Write**.

## 4. Connect GitHub → Space (Ethan, 2 min)
GitHub repo **43v3r333/43v3rB3tz** → Settings → Secrets and variables → Actions:
- **Secret** `HF_TOKEN` = the HF write token
- **Variable** `HF_SPACE` = `<your-hf-username>/43v3rb3tz-api`

Then Actions → **Deploy backend to Hugging Face Space** → Run workflow. The first build takes about 15 min (ML packages).

## 5. Switch over (Claude, after Ethan says the Space is up)
- Check `https://<user>-43v3rb3tz-api.hf.space/health` and `/ops/health` (with OPS_TOKEN).
- Vercel `43v3rb3tz`: set `INTERNAL_API_URL` (and `NEXT_PUBLIC_API_URL` if it pointed at the tunnel) to the Space URL, then redeploy.
- Models are not copied from the PC's MinIO: B3tz Ops runs `sync-leagues`, `train-house-models`, `scrape-fixtures` and `generate-predictions` in the cloud.
- After a day of green checks, Ethan stops the PC stack: `docker compose down` (no `-v`, so the PC copy stays as a backup).
