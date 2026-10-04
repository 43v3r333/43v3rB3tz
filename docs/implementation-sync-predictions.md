# Implementation: incremental sync, disk guard, prediction fix

This document was generated because automated edits to non-markdown files were blocked. Apply the changes below in Agent mode or manually.

## Root cause: predictions not working

[`prophitbet-saas/backend/app/services/prediction_service.py`](prophitbet-saas/backend/app/services/prediction_service.py) calls `construct_inputs_by_fixture` with **wrong keyword arguments**. The real signature in [`src/preprocessing/utils/inputs.py`](src/preprocessing/utils/inputs.py) is:

`construct_inputs_by_fixture(df: pd.DataFrame, fixture_df: pd.DataFrame)`

where `fixture_df` must include columns `Home`, `Away`, `1`, `X`, `2`.

The service also called `model.predict()` like sklearn on a single row; ProphitBet [`ClassificationModel.predict`](src/models/model.py) expects a **DataFrame**.

**Fix:** Build a `fixture_df` with one row per match (placeholder odds if missing), sort `league_df` by `Date` descending, call `construct_inputs_by_fixture(df=league_df, fixture_df=fixture_df)` once per batch, then `model.predict(input_df)` and `model.predict_proba(input_df)`. Optionally resolve team names with `difflib` against CSV `Home`/`Away` values.

---

## 1. Config additions

In [`prophitbet-saas/backend/app/config.py`](prophitbet-saas/backend/app/config.py), add to `Settings`:

```python
SYNC_SKIP_IF_NEWER_THAN_HOURS: int = 24
SYNC_MIN_FREE_DISK_MB: int = 256
DISK_CHECK_PATH: str = "/"
```

---

## 2. Disk check helper (new file)

Create [`prophitbet-saas/backend/app/workers/sync_utils.py`](prophitbet-saas/backend/app/workers/sync_utils.py):

```python
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


def disk_free_mb(path: str) -> float:
    try:
        usage = shutil.disk_usage(Path(path))
        return usage.free / (1024 * 1024)
    except OSError as e:
        logger.warning("disk_usage failed for %s: %s", path, e)
        return float("inf")


def assert_enough_disk_for_sync(min_free_mb: int, path: str) -> tuple[bool, float]:
    if min_free_mb <= 0:
        return True, disk_free_mb(path)
    free = disk_free_mb(path)
    ok = free >= float(min_free_mb)
    if not ok:
        logger.error("Insufficient disk space: %.1f MB free on %s (need %s MB)", free, path, min_free_mb)
    return ok, free
```

---

## 3. Data sync: skip + disk

In [`data_sync.py`](prophitbet-saas/backend/app/workers/data_sync.py):

- Import `timedelta`, `get_settings`, and `assert_enough_disk_for_sync`.
- At start of `sync_all_leagues_task(self, force_resync: bool = False, skip_if_synced_within_hours: int | None = None)`:
  - Load settings; `hours = skip_if_synced_within_hours if skip_if_synced_within_hours is not None else settings.SYNC_SKIP_IF_NEWER_THAN_HOURS`.
  - If `settings.SYNC_MIN_FREE_DISK_MB > 0`: call `assert_enough_disk_for_sync(...)`; if False, return `{"error": "low_disk", ...}`.
- Inside the league loop, before `_sync_one_league`:
  - If not `force_resync` and `hours > 0` and `lg.last_synced_at` is not None:
    - Query `LeagueDataset` for this `lg.id`; if exists and `(now - last_synced_at) < timedelta(hours=hours)`, log and **continue** (skip).

Pass the same skip logic into `sync_single_league_by_id` only if you want (result worker usually needs fresh data — **do not skip** in `sync_single_league_by_id` by default).

---

## 4. Admin API query params

In [`admin.py`](prophitbet-saas/backend/app/api/admin.py), change `trigger_league_sync` to:

```python
@router.post("/sync-leagues")
async def trigger_league_sync(
    force: bool = Query(False),
    skip_if_synced_within_hours: Optional[int] = Query(None, ge=0, le=8760),
    _admin: User = Depends(require_admin),
):
    from backend.app.workers.data_sync import sync_all_leagues_task
    kwargs = {"force_resync": force}
    if skip_if_synced_within_hours is not None:
        kwargs["skip_if_synced_within_hours"] = skip_if_synced_within_hours
    job = sync_all_leagues_task.delay(**kwargs)
    return {"job_id": job.id, "message": "League data sync triggered", "kwargs": kwargs}
```

Add `Optional` to imports if missing.

---

## 5. Replace `prediction_service.py`

Replace the body of `generate_predictions_for_league` with the batch implementation described in section 1 (construct `fixture_df`, sort `league_df`, `construct_inputs_by_fixture`, `model.predict` / `predict_proba` on full `input_df`, map rows back to home_raw/away_raw for API output).

---

## 6. Celery beat (optional)

In [`celery_app.py`](prophitbet-saas/backend/app/workers/celery_app.py), for `sync-league-data-daily`, you can pass kwargs if your Celery version supports it in beat schedule, or rely on env default `SYNC_SKIP_IF_NEWER_THAN_HOURS=24` inside the task.

---

## 7. Test order (manual)

1. `docker compose up -d` in `prophitbet-saas/`
2. `docker compose exec backend python -m backend.seed`
3. POST `/admin/sync-leagues?force=true` (full sync once) or default `skip` for incremental
4. `/admin/train-house-models`
5. `/admin/scrape-fixtures`
6. `/admin/generate-predictions`
7. GET `/predictions/today` or `/docs` — verify prediction rows in DB

---

## 8. Space / MinIO

Celery does not shrink MinIO automatically. Disk check protects the **worker container filesystem**. For MinIO volume growth, use **incremental sync skip** + periodic bucket lifecycle policies outside the app, or document `mc ilm` / manual cleanup of old object versions.

---

## Appendix: full replacement `prediction_service.py`

Save as [`prophitbet-saas/backend/app/services/prediction_service.py`](prophitbet-saas/backend/app/services/prediction_service.py):

```python
import difflib
import logging
import pickle

import pandas as pd

from backend.app.config import setup_ml_path

logger = logging.getLogger(__name__)

_DEFAULT_ODDS = {"1": 2.2, "X": 3.2, "2": 3.2}


def _resolve_team_name(name: str, column: pd.Series) -> str:
    name = (name or "").strip()
    uniq = [str(u).strip() for u in column.dropna().unique()]
    if name in uniq:
        return name
    close = difflib.get_close_matches(name, uniq, n=1, cutoff=0.75)
    if close:
        return close[0]
    for u in uniq:
        if name.lower() in u.lower() or u.lower() in name.lower():
            return u
    return name


def generate_predictions_for_league(
    model_bytes: bytes,
    league_df: pd.DataFrame,
    fixtures: list[dict],
    target_type: str = "result",
) -> list[dict]:
    setup_ml_path()
    from src.preprocessing.utils.inputs import construct_inputs_by_fixture
    from src.preprocessing.utils.target import TargetType

    model = pickle.loads(model_bytes)
    tt = TargetType.RESULT if target_type == "result" else TargetType.OVER_UNDER
    results: list[dict] = []

    if league_df is None or league_df.empty or "Date" not in league_df.columns:
        logger.warning("generate_predictions_for_league: invalid league_df")
        return results

    df = league_df.sort_values("Date", ascending=False).reset_index(drop=True)
    rows = []
    raw_pairs = []
    for fixture in fixtures:
        home_raw = fixture["home_team"]
        away_raw = fixture["away_team"]
        home = _resolve_team_name(home_raw, df["Home"])
        away = _resolve_team_name(away_raw, df["Away"])
        rows.append(
            {
                "Home": home,
                "Away": away,
                "1": _DEFAULT_ODDS["1"],
                "X": _DEFAULT_ODDS["X"],
                "2": _DEFAULT_ODDS["2"],
            }
        )
        raw_pairs.append((home_raw, away_raw))

    fixture_df = pd.DataFrame(rows)
    try:
        input_df = construct_inputs_by_fixture(df=df, fixture_df=fixture_df)
    except Exception as e:
        logger.error("construct_inputs_by_fixture failed: %s", e)
        return results

    try:
        y_pred, _ = model.predict(input_df)
        proba = model.predict_proba(input_df)
    except Exception as e:
        logger.error("model.predict failed: %s", e)
        return results

    if tt == TargetType.RESULT:
        labels = ["A", "D", "H"]
        nlab = 3
    else:
        labels = ["Under", "Over"]
        nlab = 2

    for i, (home_raw, away_raw) in enumerate(raw_pairs):
        try:
            predicted = labels[int(y_pred[i])]
            prob_dict = {
                labels[j]: round(float(proba[i][j]), 4)
                for j in range(min(nlab, proba.shape[1]))
            }
        except (IndexError, ValueError) as e:
            logger.warning("prediction row %s failed: %s", i, e)
            continue
        results.append(
            {
                "home_team": home_raw,
                "away_team": away_raw,
                "predicted_result": predicted,
                "probabilities": prob_dict,
            }
        )

    return results
```
