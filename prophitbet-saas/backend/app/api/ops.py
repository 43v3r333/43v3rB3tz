"""Ops Contract for the LifeOS Business Command Center (see LifeOS repo ops/contract.md).

GET /ops/health | /ops/status | /ops/tasks and POST /ops/actions/{name}, all behind
`Authorization: Bearer <OPS_TOKEN>`. Read-only aggregate numbers: no user data, no secrets.
Reached from LifeOS via https://43v3rb3tz.vercel.app/api/proxy/ops/... (Vercel rewrite).
"""
import hmac
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db

router = APIRouter()


def require_ops_token(authorization: str = Header(default="")) -> None:
    expected = os.environ.get("OPS_TOKEN", "")
    got = authorization[7:] if authorization.startswith("Bearer ") else ""
    if not expected or not hmac.compare_digest(got.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="unauthorized")


async def _scalar(db: AsyncSession, sql: str):
    try:
        return (await db.execute(text(sql))).scalar()
    except Exception:
        await db.rollback()
        return None


@router.get("/health", dependencies=[Depends(require_ops_token)])
async def ops_health(db: AsyncSession = Depends(get_db)):
    started = time.monotonic()
    ok = await _scalar(db, "SELECT 1") == 1
    ms = round((time.monotonic() - started) * 1000)
    return {
        "ok": ok,
        "version": "1",
        "commit": (os.environ.get("GIT_COMMIT") or "")[:7] or None,
        "db": "ok" if ok else "down",
        "checks": [{"name": "database (Neon)", "ok": ok, "detail": f"{ms} ms"}],
    }


@router.get("/status", dependencies=[Depends(require_ops_token)])
async def ops_status(db: AsyncSession = Depends(get_db)):
    users = await _scalar(db, "SELECT COUNT(*) FROM users")
    pred_today = await _scalar(db, "SELECT COUNT(*) FROM predictions WHERE created_at >= date_trunc('day', now())")
    pred_7d = await _scalar(db, "SELECT COUNT(*) FROM predictions WHERE created_at > now() - interval '7 days'")
    acc_30d = await _scalar(db, "SELECT ROUND(100.0 * AVG(CASE WHEN is_correct THEN 1 ELSE 0 END), 1) FROM predictions "
                                "WHERE is_correct IS NOT NULL AND result_verified_at > now() - interval '30 days'")
    upcoming = await _scalar(db, "SELECT COUNT(*) FROM fixtures WHERE is_current AND match_date > now()")
    unpredicted = await _scalar(db, "SELECT COUNT(*) FROM fixtures WHERE is_current AND match_date > now() AND NOT predicted")
    last_fetch = await _scalar(db, "SELECT MAX(fetched_at) FROM fixtures")
    last_pred = await _scalar(db, "SELECT MAX(created_at) FROM predictions")

    now = datetime.now(timezone.utc)
    hours = lambda ts: round((now - ts).total_seconds() / 3600, 1) if ts else None  # noqa: E731
    kpis = [
        {"key": "users", "label": "Users", "value": users, "unit": ""},
        {"key": "predictions_today", "label": "Predictions today", "value": pred_today, "unit": ""},
        {"key": "predictions_7d", "label": "Predictions (7 days)", "value": pred_7d, "unit": ""},
        {"key": "accuracy_30d", "label": "Accuracy (30 days)", "value": float(acc_30d) if acc_30d is not None else None, "unit": "%"},
        {"key": "fixtures_upcoming", "label": "Upcoming fixtures", "value": upcoming, "unit": ""},
        {"key": "fixtures_unpredicted", "label": "Fixtures without prediction", "value": unpredicted, "unit": ""},
        {"key": "fixtures_age_h", "label": "Fixture data age", "value": hours(last_fetch), "unit": "h"},
        {"key": "predictions_age_h", "label": "Last prediction", "value": hours(last_pred), "unit": "h ago"},
    ]
    alerts = []
    if hours(last_fetch) is None or hours(last_fetch) > 24:
        alerts.append({"level": "warning", "message": "Fixture data is older than 24 h — run Scrape Fixtures"})
    if unpredicted:
        alerts.append({"level": "info", "message": f"{unpredicted} upcoming fixture(s) have no prediction — run Generate Predictions"})
    if acc_30d is not None and float(acc_30d) < 45:
        alerts.append({"level": "warning", "message": f"30-day accuracy is {acc_30d}% — check for model drift"})
    return {"kpis": kpis, "alerts": alerts}


@router.get("/tasks", dependencies=[Depends(require_ops_token)])
async def ops_tasks():
    # B3tz has no task table yet; progress is tracked in GitHub issues / Linear.
    return {"tasks": []}


ACTIONS: dict = {}  # whitelisted safe actions get added here; risky ones go through LifeOS approvals


@router.post("/actions/{name}", dependencies=[Depends(require_ops_token)])
async def ops_action(name: str):
    if name not in ACTIONS:
        raise HTTPException(status_code=404, detail={"error": "unknown action", "allowed": sorted(ACTIONS)})
    return {"ok": True, "result": await ACTIONS[name]()}
