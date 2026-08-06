from datetime import datetime, timedelta, timezone

from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects import sqlite as sqlite_dialect

from models import WeeklyPortfolioMetric, db

_UPSERT_BY_DIALECT = {
    "postgresql": postgresql.insert,
    "sqlite": sqlite_dialect.insert,
}


def _week_start(now=None):
    now = now or datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).date()
    return monday.isoformat()


def _insert_stub(week, observed):
    table = WeeklyPortfolioMetric.__table__
    dialect_name = db.engine.dialect.name
    insert = _UPSERT_BY_DIALECT.get(dialect_name, sqlite_dialect.insert)
    stmt = insert(table).values(
        week_start=week, completed_screenings=0, vet_searches=0, updated_at=observed
    )
    stmt = stmt.on_conflict_do_nothing(index_elements=["week_start"])
    db.session.execute(stmt)


def _increment(column, now=None):
    if column not in {"completed_screenings", "vet_searches"}:
        raise ValueError("unsupported aggregate metric")
    observed = now or datetime.now(timezone.utc)
    week = _week_start(observed)

    _insert_stub(week, observed)

    table = WeeklyPortfolioMetric.__table__
    db.session.execute(
        table.update()
        .where(table.c.week_start == week)
        .values(**{column: table.c[column] + 1, "updated_at": observed})
    )
    db.session.commit()


def record_screening(now=None):
    _increment("completed_screenings", now=now)


def record_vet_search(now=None):
    _increment("vet_searches", now=now)


def portfolio_metrics(now=None):
    observed = now or datetime.now(timezone.utc)
    week = _week_start(observed)
    metric = db.session.get(WeeklyPortfolioMetric, week)

    completed = metric.completed_screenings if metric else 0
    searches = metric.vet_searches if metric else 0
    updated_at = None
    if metric and metric.updated_at:
        # SQLite drops tzinfo on read-back for tz-aware columns (Postgres
        # keeps it); everything we write is UTC, so normalize either way.
        stored = metric.updated_at
        if stored.tzinfo is None:
            stored = stored.replace(tzinfo=timezone.utc)
        updated_at = stored.isoformat()

    return {
        "privacy": "aggregate_only",
        "window": "calendar_week_utc",
        "completedScreeningsWithGuidanceWeekly": int(completed),
        "vetSearchesWeekly": int(searches),
        "latestAggregateUpdateAt": updated_at,
        "rawImageRetention": "none",
        "locationRetention": "none",
    }
