import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_METRICS_PATH = os.environ.get(
    "METRICS_DB_PATH",
    "/tmp/poopsense-portfolio-metrics.sqlite3",
)


def _week_start(now=None):
    now = now or datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).date()
    return monday.isoformat()


def _connect(path=None):
    selected = Path(path or DEFAULT_METRICS_PATH)
    selected.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(selected, timeout=10)
    connection.execute(
        """
        create table if not exists weekly_portfolio_metrics (
          week_start text primary key,
          completed_screenings integer not null default 0,
          vet_searches integer not null default 0,
          updated_at text not null
        )
        """
    )
    return connection


def _increment(column, path=None, now=None):
    if column not in {"completed_screenings", "vet_searches"}:
        raise ValueError("unsupported aggregate metric")
    observed = now or datetime.now(timezone.utc)
    week = _week_start(observed)
    with _connect(path) as connection:
        connection.execute(
            """
            insert into weekly_portfolio_metrics
              (week_start, completed_screenings, vet_searches, updated_at)
            values (?, 0, 0, ?)
            on conflict(week_start) do nothing
            """,
            (week, observed.isoformat()),
        )
        connection.execute(
            f"""
            update weekly_portfolio_metrics
            set {column} = {column} + 1, updated_at = ?
            where week_start = ?
            """,
            (observed.isoformat(), week),
        )


def record_screening(path=None, now=None):
    _increment("completed_screenings", path=path, now=now)


def record_vet_search(path=None, now=None):
    _increment("vet_searches", path=path, now=now)


def portfolio_metrics(path=None, now=None):
    observed = now or datetime.now(timezone.utc)
    with _connect(path) as connection:
        row = connection.execute(
            """
            select completed_screenings, vet_searches, updated_at
            from weekly_portfolio_metrics
            where week_start = ?
            """,
            (_week_start(observed),),
        ).fetchone()
    completed, searches, updated_at = row or (0, 0, None)
    return {
        "privacy": "aggregate_only",
        "window": "calendar_week_utc",
        "completedScreeningsWithGuidanceWeekly": int(completed),
        "vetSearchesWeekly": int(searches),
        "latestAggregateUpdateAt": updated_at,
        "rawImageRetention": "none",
        "locationRetention": "none",
    }
