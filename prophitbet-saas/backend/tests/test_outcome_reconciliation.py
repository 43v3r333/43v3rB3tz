import unittest
from datetime import datetime, timezone
import pandas as pd
from backend.app.services.team_mapping import normalize_team_name
from backend.app.workers.results import _find_match_result


class OutcomeReconciliationTests(unittest.TestCase):
    def test_reverse_explicit_alias(self):
        self.assertEqual(normalize_team_name('Manchester United', ['Man United'], allow_fuzzy=False), 'Man United')

    def test_similar_names_are_not_evidence(self):
        self.assertIsNone(normalize_team_name('Manchester Utd Women', ['Man United'], allow_fuzzy=False))

    def test_conflicting_scores_are_rejected(self):
        rows = pd.DataFrame([dict(Date='2026-01-01', Home='Home', Away='Away', HG=1, AG=0, Result='H'),
                             dict(Date='2026-01-01', Home='Home', Away='Away', HG=2, AG=0, Result='H')])
        self.assertIsNone(_find_match_result(rows, 'Home', 'Away', datetime(2026, 1, 1, tzinfo=timezone.utc)))

    def test_non_integer_scores_are_rejected(self):
        rows = pd.DataFrame([dict(Date='2026-01-01', Home='Home', Away='Away', HG=1.5, AG=0, Result='H')])
        self.assertIsNone(_find_match_result(rows, 'Home', 'Away', datetime(2026, 1, 1, tzinfo=timezone.utc)))
