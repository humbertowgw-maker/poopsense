import unittest
from datetime import datetime, timezone

from app import app
from metrics import portfolio_metrics, record_screening, record_vet_search
from models import db


class AggregateMetricsTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_counts_completed_guidance_without_storing_images_or_location(self):
        now = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)
        record_screening(now=now)
        record_screening(now=now)
        record_vet_search(now=now)

        metrics = portfolio_metrics(now=now)

        self.assertEqual(metrics, {
            "privacy": "aggregate_only",
            "window": "calendar_week_utc",
            "completedScreeningsWithGuidanceWeekly": 2,
            "vetSearchesWeekly": 1,
            "latestAggregateUpdateAt": now.isoformat(),
            "rawImageRetention": "none",
            "locationRetention": "none",
        })
        self.assertNotIn("image", {
            key.lower()
            for key in metrics
            if key not in {"rawImageRetention"}
        })
        self.assertNotIn("latitude", metrics)
        self.assertNotIn("longitude", metrics)

    def test_metrics_persist_in_the_shared_database_table(self):
        now = datetime(2026, 8, 3, 9, tzinfo=timezone.utc)
        record_screening(now=now)

        from models import WeeklyPortfolioMetric
        row = db.session.get(WeeklyPortfolioMetric, "2026-08-03")

        self.assertIsNotNone(row)
        self.assertEqual(row.completed_screenings, 1)
        self.assertEqual(row.vet_searches, 0)


if __name__ == "__main__":
    unittest.main()
