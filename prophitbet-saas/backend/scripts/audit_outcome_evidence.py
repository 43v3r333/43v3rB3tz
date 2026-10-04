"""Audit outcomes against stored league data; --apply repairs exact matches with a backup.

The default is read-only. Stored datasets are reconciliation evidence, not an
independent guarantee of provider accuracy. Unmatched outcomes stay unverified.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from backend.app.config import setup_ml_path
from backend.app.db.models import Prediction, LeagueDataset
from backend.app.workers.results import _get_sync_session, _prepare_result_dates, _find_match_result
from backend.app.services.league_service import _load_csv_from_s3_sync


def classify_match(pred, match):
    if match is None:
        return 'unmatched'
    if match['result'] == pred.actual_result and match['score'] == pred.actual_score:
        return 'consistent'
    return 'conflicting'


def apply_match(pred, match, dataset):
    """Return the previous state before applying a source-backed correction."""
    change = {
        'id': str(pred.id),
        'previous': {
            'actual_result': pred.actual_result, 'actual_score': pred.actual_score,
            'is_correct': pred.is_correct, 'result_source': pred.result_source,
            'result_verified_at': str(pred.result_verified_at),
        },
        'evidence': {'dataset_id': str(dataset.id), 'file_path': dataset.file_path, 'match': match},
    }
    pred.actual_result = match['result']
    pred.actual_score = match['score']
    pred.is_correct = pred.predicted_result == match['result']
    pred.result_source = f'league_dataset:{dataset.id}:{dataset.file_path}:{match["date"]}'
    pred.result_verified_at = datetime.now(timezone.utc)
    return change


def sample_mismatch(pred, match, df):
    columns = ['Home', 'HomeTeam', 'Away', 'AwayTeam', 'Result', 'HG', 'AG', 'FTR', 'FTHG', 'FTAG']
    same_day = df.loc[df['_verified_match_date'].dt.date == pred.match_date.date()]
    return {
        'league_id': pred.league_id, 'home': pred.home_team, 'away': pred.away_team,
        'date': str(pred.match_date), 'stored_result': pred.actual_result,
        'stored_score': pred.actual_score, 'candidate': match,
        'source_day_matches': same_day[[c for c in columns if c in same_day]].head(10).to_dict('records'),
    }


def reconcile_league(rows, dataset, report, apply):
    df = _prepare_result_dates(_load_csv_from_s3_sync(dataset.file_path))
    report['coverage'].append({
        'league_id': dataset.league_id, 'rows': len(df),
        'first': str(df['_verified_match_date'].min()),
        'last': str(df['_verified_match_date'].max()),
    })
    for pred in rows:
        match = _find_match_result(df, pred.home_team, pred.away_team, pred.match_date, pred.market_type)
        state = classify_match(pred, match)
        report['counts'][state] += 1
        if state != 'consistent' and len(report['samples']) < 15:
            report['samples'].append(sample_mismatch(pred, match, df))
        if match is not None and apply:
            report['changes'].append(apply_match(pred, match, dataset))


def save_changes(session, changes, folder):
    if not changes:
        return
    folder.mkdir(parents=True, exist_ok=True)
    backup = folder / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    # Successful evidence persistence precedes the commit.
    with backup.open('x', encoding='utf-8') as stream:
        json.dump(changes, stream)
    session.commit()


def audit(session, apply=False, backup_folder=Path('/app/storage/outcome-reconciliation')):
    rows = session.query(Prediction).filter(
        Prediction.actual_result.isnot(None),
        Prediction.result_source.is_(None) | Prediction.result_verified_at.is_(None),
    ).all()
    report = {'total': len(rows), 'counts': Counter(), 'samples': [], 'coverage': [], 'changes': []}
    for league_id in sorted({p.league_id for p in rows}):
        league_rows = [p for p in rows if p.league_id == league_id]
        dataset = session.query(LeagueDataset).filter_by(league_id=league_id).order_by(
            LeagueDataset.created_at.desc()).first()
        if dataset is None:
            report['counts']['missing_dataset'] += len(league_rows)
            continue
        reconcile_league(league_rows, dataset, report, apply)
    changes = report.pop('changes')
    save_changes(session, changes, backup_folder)
    report['updated'] = len(changes)
    return report


def main(apply=False):
    setup_ml_path()
    with _get_sync_session() as session:
        print(json.dumps(audit(session, apply), default=str))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Repair only source-matched outcomes; preserve previous values in storage.')
    main(parser.parse_args().apply)
