# System audit — 43v3rB3tz

## Verified findings

- API health responds successfully; all 11 Prometheus scrape targets were up.
- Database: 26,210 fixtures, 4,743 current upcoming fixtures at inspection; no current fixture missing source URL or fetched timestamp. This is a completeness check, not independent verification of every fixture.
- Database: 8,112 predictions; 612 outcome records still lack source/verification evidence after one exact-match reconciliation. These must not be treated as verified results.
- SA bookmaker odds table remains empty. A fresh Betway observation yielded 70 event blocks: 60 parsed football events and 10 rejected virtual events. None matched a unique fresh stored fixture. Hollywoodbets returned an explicit empty event state. Raw observations are not usable fixture-linked odds.
- Running backend previously had stale code. The rebuilt/deployed backend now passes all 116 regressions.
- Latest SonarQube scan completed and server processing succeeded at 12:49:54 SAST. Quality gate still FAILED: new-code coverage 34.4% (80% required), 10 new violations (zero required), and new-code duplication 0.13414% (passes the 3% limit). The preceding scan reported zero coverage and 17 new violations. Analysis ID: `1ab50db6-2801-4ecf-8377-4d03df69a264`.

## Implemented corrections

- Reject incomplete, nonfinite, or unnormalised MiroFish match probabilities and invalid decimal odds.
- Exclude kickoff-day and later history from MiroFish input statistics.
- Exclude unsourced tactical prose and cross-team vector substitutions.
- Version MiroFish evidence policy; older cached reports are not reused or listed as current-policy reports.
- MiroFish configuration no longer claims verified readiness.
- Calibration requires verified results, pre-kickoff simulations, and current evidence-policy reports. Missing evaluation data no longer becomes 25% accuracy or a default winning agent.
- Removed fabricated calibration counts, accuracy percentages and weights from the MiroFish UI.
- Removed unreachable generated live-timeline code; missing live-event provider still returns an explicit unavailable response.
- Odds worker reports unavailable feeds as warnings and propagates unexpected exceptions instead of reporting successful Celery tasks.
- Scanner helper no longer prints generated tokens or embeds token values in the Docker command arguments.
- Result reconciliation now accepts explicit reverse aliases, rejects fuzzy team matches, conflicting source scores and fractional goals.
- The opt-in reconciliation script archived prior values before correcting Brighton–Manchester United on 2026-05-24 from 1–2 to the stored dataset's 0–3. The other 612 records were preserved, not guessed or deleted.
- Replaced the hanging bookmaker browser wrapper with standard Playwright/Edge. Betway kickoff parsing now accepts matching sibling links and rejects conflicting schedules.
- Fixed several new Sonar findings and verified successful import of real backend coverage. Remaining new findings concern team-alias complexity, reconciliation-script complexity/style, and S3 expected-owner validation. No quality-gate thresholds or source exclusions were weakened.
- Removed the frontend's build-time Google font dependency after its network fetch failed; the UI uses system fonts.

## Validation

- 116 backend tests passed in an isolated container using current source; a real coverage XML report was generated.
- The same 116 tests passed inside the deployed backend. Backend/shared-source line coverage is 40.83% (3,113 / 7,625 lines); this is not Sonar's new-code coverage metric.
- 19 frontend league-identity/grouping regressions passed.
- TypeScript checking passed.
- Frontend production build passed and was deployed; `/login` returned HTTP 200. API `/health` returned `ok`, and all 11 Prometheus targets were up after deployment.
- CI now generates and uploads backend coverage using the tested container command; workflow YAML validated locally. GitHub Actions has not been run for these unpushed changes.
- No production records were deleted or fabricated to silence alerts.

## Open work / limits

- Source reconciliation for 612 historical outcomes; coverage overlap between fresh bookmaker events and verified stored fixtures.
- MiroFish external endpoint availability and LLM configuration need verification. Configuration is not readiness.
- JEv provider access remains unavailable; deterministic checks do not substitute for its AI review.
- Triage remaining Sonar findings, including credential defaults, async blocking IO, accessibility and desktop code. Do not automatically apply cloud-S3-specific findings to local MinIO.
- Increase measured new-code coverage from 34.4% to the required 80% and resolve the remaining 10 new findings. Frontend coverage is not yet imported. Sonar also reports missing blame information for 33 dirty/new files.
- Broader MiroFish demo/sandbox rendering, seeded dossiers, and statistical methods still require review. This audit is not a certification that all app features or all data are correct.
- Authenticated end-to-end browser workflows and independent fixture/result accuracy checks remain to be completed.
- Startup logs still warn that Celery runs as root and that `next start` is used with Next.js standalone output. Services respond, but these deployment warnings remain open.
