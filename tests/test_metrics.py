import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from metrics import portfolio_metrics, record_screening, record_vet_search


class AggregateMetricsTests(unittest.TestCase):
    def test_counts_completed_guidance_without_storing_images_or_location(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metrics.sqlite3"
            now = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)
            record_screening(path=path, now=now)
            record_screening(path=path, now=now)
            record_vet_search(path=path, now=now)

            metrics = portfolio_metrics(path=path, now=now)

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


if __name__ == "__main__":
    unittest.main()
