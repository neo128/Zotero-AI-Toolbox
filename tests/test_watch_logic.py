import datetime as dt
import pathlib
import sys
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import watch_and_import_papers as watch  # noqa: E402


class WatchLogicTest(unittest.TestCase):
    def test_parse_args_defaults(self) -> None:
        with patch.object(sys, "argv", ["watch_and_import_papers.py"]):
            args = watch.parse_args()
        self.assertEqual(args.tags, "tag.json")
        self.assertEqual(args.since_days, 0)
        self.assertAlmostEqual(args.since_hours, 24.0)
        self.assertEqual(args.top_k, 10)
        self.assertAlmostEqual(args.min_score, 0.3)
        self.assertFalse(args.no_hf_papers)
        self.assertAlmostEqual(args.hf_weight, 0.3)

    def test_parse_args_overrides(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "watch_and_import_papers.py",
                "--since-hours",
                "12",
                "--top-k",
                "5",
                "--min-score",
                "0.7",
                "--no-hf-papers",
                "--hf-weight",
                "0.1",
            ],
        ):
            args = watch.parse_args()
        self.assertAlmostEqual(args.since_hours, 12.0)
        self.assertEqual(args.top_k, 5)
        self.assertAlmostEqual(args.min_score, 0.7)
        self.assertTrue(args.no_hf_papers)
        self.assertAlmostEqual(args.hf_weight, 0.1)

    def test_compute_score_recency_and_hf(self) -> None:
        now = dt.datetime(2026, 2, 9, tzinfo=dt.timezone.utc)
        today = now.date().isoformat()
        old = "2025-01-01"

        cand_new = watch.Candidate(
            title="new",
            authors=[],
            date=today,
            year="2026",
            url=None,
            pdf_url=None,
            doi=None,
            arxiv_id=None,
            abstract=None,
            source="test",
            hf_score=0.0,
            tags=set(),
            collections=set(),
        )
        cand_old = watch.Candidate(
            title="old",
            authors=[],
            date=old,
            year="2025",
            url=None,
            pdf_url=None,
            doi=None,
            arxiv_id=None,
            abstract=None,
            source="test",
            hf_score=0.0,
            tags=set(),
            collections=set(),
        )

        score_new = watch.compute_score(now, cand_new, max_days=30, cit=0, inf_cit=0, hf_weight=0.0)
        score_old = watch.compute_score(now, cand_old, max_days=30, cit=0, inf_cit=0, hf_weight=0.0)
        self.assertGreater(score_new, score_old)
        self.assertAlmostEqual(score_new, 0.5, places=3)

        cand_hf = watch.Candidate(
            title="hf",
            authors=[],
            date=today,
            year="2026",
            url=None,
            pdf_url=None,
            doi=None,
            arxiv_id=None,
            abstract=None,
            source="test",
            hf_score=1.0,
            tags=set(),
            collections=set(),
        )
        score_hf = watch.compute_score(now, cand_hf, max_days=30, cit=0, inf_cit=0, hf_weight=0.3)
        self.assertAlmostEqual(score_hf, 0.8, places=3)

    def test_compute_score_is_capped(self) -> None:
        now = dt.datetime(2026, 2, 9, tzinfo=dt.timezone.utc)
        cand = watch.Candidate(
            title="cap",
            authors=[],
            date=now.date().isoformat(),
            year="2026",
            url=None,
            pdf_url=None,
            doi=None,
            arxiv_id=None,
            abstract=None,
            source="test",
            hf_score=1.0,
            tags=set(),
            collections=set(),
        )
        score = watch.compute_score(now, cand, max_days=1, cit=999, inf_cit=999, hf_weight=1.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
