import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

import pandas as pd
from botocore.exceptions import ClientError

from backend.app.services.league_service import bucket_owner_condition, dataset_objects_status
from backend.app.services.bookmaker_feed import select_fixture_match
from backend.app.services.team_mapping import normalize_team_name
from backend.app.workers.results import _find_match_result
from backend.scripts.audit_outcome_evidence import audit, save_changes


class StorageOwnershipTests(unittest.TestCase):
    def settings(self, endpoint='http://minio:9000', owner=''):
        return SimpleNamespace(S3_ENDPOINT=endpoint, S3_EXPECTED_BUCKET_OWNER=owner,
                               S3_ACCESS_KEY='test', S3_SECRET_KEY='test', S3_BUCKET='test')

    def test_private_store_needs_no_aws_account(self):
        self.assertEqual(bucket_owner_condition(self.settings()), {})

    def test_aws_requires_owner(self):
        for endpoint in ('', 'https://s3.amazonaws.com', 'https://s3.cn-north-1.amazonaws.com.cn'):
            settings = self.settings(endpoint)
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                bucket_owner_condition(settings)

    def test_configured_owner_and_invalid_owner(self):
        self.assertEqual(bucket_owner_condition(self.settings(owner='123456789012')),
                         {'ExpectedBucketOwner': '123456789012'})
        for owner in ('1', 'abcdefghijkl', '１２３４５６７８９０１２'):
            settings = self.settings(owner=owner)
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                bucket_owner_condition(settings)

    def test_storage_errors_are_not_reported_as_absent(self):
        def head(**kwargs):
            key = kwargs['Key']
            if key == 'present':
                return {'ContentLength': 12}
            if key == 'empty':
                return {'ContentLength': 0}
            raise ClientError({'Error': {'Code': key}}, 'HeadObject')
        client = Mock()
        client.head_object.side_effect = head
        with patch('boto3.client', return_value=client), patch(
                'backend.app.config.get_settings', return_value=self.settings(owner='123456789012')):
            result = dataset_objects_status(['present', 'empty', '404', 'AccessDenied', None])
        self.assertEqual(result, {'present': 1, 'empty': 0, '404': 0, 'AccessDenied': None, None: 0})
        self.assertTrue(all(call.kwargs['ExpectedBucketOwner'] == '123456789012'
                            for call in client.head_object.call_args_list))


class FixtureAliasTests(unittest.TestCase):
    def test_observed_spanish_bookmaker_aliases(self):
        for bookmaker, fixture in (('Sporting Gijon', 'Sporting Gijón'),
                                   ('CD Castellon', 'Castellón'), ('AD Ceuta', 'Ceuta')):
            self.assertEqual(normalize_team_name(bookmaker, [fixture], allow_fuzzy=False), fixture)

    def test_alias_matching_rejects_ambiguous_or_different_teams(self):
        fixture = SimpleNamespace(home_team='Manchester United', away_team='Manchester City')
        row = {'home_team': 'Man United', 'away_team': 'Man City'}
        self.assertEqual(select_fixture_match([(fixture, 'Premier League')], row), (fixture, 'Premier League'))
        self.assertIsNone(select_fixture_match([(fixture, 'A'), (fixture, 'B')], row))
        row['home_team'] = 'Manchester United Women'
        self.assertIsNone(select_fixture_match([(fixture, 'Premier League')], row))

    def test_strict_and_legacy_name_paths(self):
        for raw in ('', ' ', None):
            self.assertIsNone(normalize_team_name(raw, ['Manchester United']))
        self.assertEqual(normalize_team_name('Man United', ['Manchester United']), 'Manchester United')
        self.assertEqual(normalize_team_name('man united', ['Manchester United']), 'Manchester United')
        self.assertEqual(normalize_team_name('Example', ['example']), 'example')
        self.assertIsNone(normalize_team_name('Unrelated', ['Example'], allow_fuzzy=False))
        self.assertEqual(normalize_team_name('Examplee', ['Example']), 'Example')
        self.assertEqual(normalize_team_name('Long', ['Long Football Club']), 'Long Football Club')
        self.assertIsNone(normalize_team_name('ZZZZZ', ['Example']))

    def test_malformed_scores_fail_closed(self):
        for value in ('unknown', float('inf'), -1, 1.5):
            df = pd.DataFrame([{'Date': '2026-01-01', 'Home': 'A', 'Away': 'B',
                                'HG': value, 'AG': 0, 'Result': 'H'}])
            self.assertIsNone(_find_match_result(df, 'A', 'B', datetime(2026, 1, 1, tzinfo=timezone.utc)))


class ReconciliationAuditTests(unittest.TestCase):
    def setUp(self):
        self.pred = SimpleNamespace(id='prediction', league_id=6, home_team='A', away_team='B',
            match_date=datetime(2026, 1, 1, tzinfo=timezone.utc), market_type='result',
            actual_result='A', actual_score='0-1', is_correct=False, result_source=None,
            result_verified_at=None, predicted_result='H')
        self.dataset = SimpleNamespace(id='dataset', league_id=6, file_path='test.csv')
        self.df = pd.DataFrame([{'Date': '2026-01-01', 'Home': 'A', 'Away': 'B', 'HG': 2, 'AG': 0, 'Result': 'H'}])
        self.session = Mock()
        self.session.query.return_value.filter.return_value.all.return_value = [self.pred]
        self.session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = self.dataset

    def test_read_only_audit_never_changes_prediction(self):
        with patch('backend.scripts.audit_outcome_evidence._load_csv_from_s3_sync', return_value=self.df):
            report = audit(self.session)
        self.assertEqual(report['updated'], 0)
        self.assertEqual(report['counts']['conflicting'], 1)
        self.assertEqual(self.pred.actual_score, '0-1')
        self.session.commit.assert_not_called()

    def test_apply_preserves_previous_values_before_commit(self):
        with TemporaryDirectory() as folder, patch(
                'backend.scripts.audit_outcome_evidence._load_csv_from_s3_sync', return_value=self.df):
            def verify_backup():
                backup = json.loads(next(Path(folder).glob('*.json')).read_text())
                self.assertEqual(backup[0]['previous']['actual_score'], '0-1')
            self.session.commit.side_effect = verify_backup
            report = audit(self.session, apply=True, backup_folder=Path(folder))
        self.assertEqual(report['updated'], 1)
        self.assertEqual(report['samples'][0]['stored_score'], '0-1')
        self.assertEqual(self.pred.actual_score, '2-0')
        self.assertTrue(self.pred.is_correct)
        self.session.commit.assert_called_once()

    def test_unmatched_and_consistent_outcomes(self):
        for day, score, result, expected in ((2, '0-1', 'A', 'unmatched'), (1, '2-0', 'H', 'consistent')):
            self.pred.match_date = datetime(2026, 1, day, tzinfo=timezone.utc)
            self.pred.actual_score, self.pred.actual_result = score, result
            with patch('backend.scripts.audit_outcome_evidence._load_csv_from_s3_sync', return_value=self.df):
                report = audit(self.session)
            self.assertEqual(report['counts'][expected], 1)

    def test_missing_dataset_and_backup_failure(self):
        self.session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = None
        self.assertEqual(audit(self.session)['counts']['missing_dataset'], 1)
        with TemporaryDirectory() as folder:
            with patch.object(Path, 'open', side_effect=OSError('read-only')):
                with self.assertRaises(OSError):
                    save_changes(self.session, [{'test': 'evidence'}], Path(folder))
        self.session.commit.assert_not_called()
