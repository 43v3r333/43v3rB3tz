import unittest
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

import pandas as pd

from backend.app.services.mirofish_service import build_match_dossier
from backend.app.services.vector_rag_service import QdrantVectorRAGService


class MiroFishEvidenceTests(unittest.TestCase):
    def prediction(self, probabilities):
        return SimpleNamespace(probabilities=probabilities, match_date=datetime(2026, 9, 20, 15, tzinfo=timezone.utc), home_team="Home", away_team="Away")

    def test_missing_probabilities_are_not_invented(self):
        prediction = self.prediction({"H": .5})
        with self.assertRaisesRegex(ValueError, "Complete"):
            build_match_dossier(prediction)

    def test_invalid_probabilities_are_rejected(self):
        for probs in ({"H": float("nan"), "D": .3, "A": .2}, {"H": .8, "D": .4, "A": .2}):
            prediction = self.prediction(probs)
            with self.subTest(probs=probs), self.assertRaisesRegex(ValueError, "finite"):
                build_match_dossier(prediction)

    def test_invalid_odds_are_rejected(self):
        prediction = self.prediction({"H": .5, "D": .3, "A": .2})
        fixture = SimpleNamespace(odds_1=0, odds_x=3, odds_2=4)
        with self.assertRaisesRegex(ValueError, "decimal"):
            build_match_dossier(prediction, fixture=fixture)

    def test_history_excludes_kickoff_day_and_future(self):
        df = pd.DataFrame({"Date": ["2026-09-19", "2026-09-20", "2026-09-21"]})
        prediction = self.prediction({"H": .5, "D": .3, "A": .2})
        fixture = SimpleNamespace(odds_1=2, odds_x=3, odds_2=4)
        with patch("backend.app.services.mirofish_service.extract_team_stats_from_dataset", side_effect=ValueError("stop after filtering")) as extract:
            with self.assertRaisesRegex(ValueError, "stop after filtering"):
                build_match_dossier(prediction, fixture=fixture, league_df=df)
            self.assertEqual(extract.call_args.kwargs["df"]["Date"].tolist(), ["2026-09-19"])


class CalibrationEvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_no_results_do_not_invent_accuracy(self):
        db = AsyncMock()
        result = MagicMock()
        result.all.return_value = []
        db.execute.return_value = result
        report = await QdrantVectorRAGService.evaluate_closed_loop_agent_calibration(db)
        self.assertEqual(report["total_settled_simulations_evaluated"], 0)
        self.assertIsNone(report["highest_performing_agent"])
        self.assertEqual(report["calibrated_weights"], {})
        self.assertEqual(report["recalibration_status"], "insufficient_evidence")
        self.assertTrue(all(p["accuracy_pct"] is None for p in report["agent_performance"].values()))
