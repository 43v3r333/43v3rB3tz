# Architecture reference (ProphitBet)

Companion to root [`AGENTS.md`](../AGENTS.md). Deeper data-flow diagrams for agents and maintainers.

## SaaS data pipeline

```mermaid
flowchart TD
  subgraph ingest [League_data]
    DL[Downloaders_main_extra]
    SE[StatisticsEngine]
    S3[MinIO_CSV]
    DS[league_datasets_table]
    DL --> SE --> S3
    SE --> DS
  end

  subgraph models [Models]
    TR[train_house_models_task]
    TM[trained_models_table]
    PKL[pickle_on_S3]
    TR --> TM --> PKL
  end

  subgraph preds [Predictions]
    FX[scrape_fixtures_task]
    FIX[fixtures_table]
    GEN[generate_daily_predictions_task]
    PRED[predictions_table]
    FX --> FIX
    GEN --> PRED
  end

  DS --> TR
  DS --> GEN
  PKL --> GEN
  FIX --> GEN
```

## Request path (user-facing)

```mermaid
sequenceDiagram
  participant U as User
  participant N as Nextjs
  participant A as FastAPI
  participant DB as Postgres
  participant S3 as MinIO

  U->>N: Browser
  N->>A: REST_JSON_JWT
  A->>DB: Async_queries
  A->>S3: Models_CSVs_optional
  A-->>N: JSON
```

## Desktop vs SaaS ML boundary

- **Single implementation** of statistics, features, and sklearn pipelines: [`src/`](../src/).
- **SaaS** loads the same code by setting `PYTHONPATH` / `ML_CORE_PATH` so `import src.*` resolves inside containers.
- **Thin layers** in `prophitbet-saas/backend/app/services/` adapt DataFrames, S3 bytes, and Celery jobs — they should not reimplement feature logic.

## Failure modes to remember

- **Sync** can be slow (many leagues) and may skip leagues with CSV/schema issues; check Celery logs.
- **FootyStats** HTML differs between desktop Selenium and SaaS httpx parsers; change both if the site structure shifts.
- **Predictions** need house models + non-empty upcoming fixtures + synced datasets per league.
