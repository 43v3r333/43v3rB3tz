# Fixture data integrity

The SaaS publishes provider-sourced schedules, not generated fixture dates.
Predictions and MiroFish forecasts remain estimates, not verified match outcomes.

## Admin workflow

1. Run **Scrape Fixtures** in Admin and wait for the job to finish.
2. Read the completion summary: it distinguishes observed fixtures, new rows,
   refreshed leagues and unavailable leagues. Partial coverage is not full success.
3. View Fixtures. Kickoffs display in SAST (UTC+2), with a source link and last
   checked time. Provider schedules can still change, particularly distant games.
4. Generate predictions only when trained models and verified odds are available.
   A schedule feed does not necessarily supply odds.

## Publication rules

- Store timezone-aware kickoffs in UTC; never infer missing dates from page order.
- Reject past, timezone-less, unsourced and duplicate upcoming fixture rows.
- A successful nonempty league refresh retires the previous snapshot without
  deleting records. Only observed team pairings and kickoffs are reactivated.
- Failed/empty feeds preserve stored rows, but public upcoming views require a
  snapshot checked within 48 hours. Scheduled refreshes run every six hours.
- Upcoming predictions require an exact league, teams and kickoff match to a
  current, fresh fixture. Rescheduled legacy predictions stay stored but hidden.
- Historical results require a score, result source and verification timestamp.
- Kickoff time alone cannot establish that a match is live. The live-events
  endpoint remains unavailable without a verified live-event provider.

## Provider configuration

Set `FOOTBALL_DATA_API_KEY` in `prophitbet-saas/.env` for football-data.org.
`API_FOOTBALL_KEY` is a different provider's credential, not an alias.
Recreate backend, celery-worker and celery-beat after changing environment values.
Free provider access may exclude current seasons or some competitions. Do not
fill those gaps with synthetic schedules, scores or odds.

## Regression checks

From `prophitbet-saas`:

```sh
docker compose exec -T backend python -m unittest backend.tests.test_fixture_integrity backend.tests.test_prediction_integrity -v
```

The September 18–19, 2026 audit refreshed 2,660 upcoming fixtures across ten
leagues, with 24 leagues unavailable. A repeat refresh inserted zero new rows.
Nine FixtureDownload league snapshots exactly matched their source feed's team
pairings and UTC dates. This checks ingestion fidelity, not independent proof
that a provider has final kickoff times. Counts naturally decrease after kickoff.
