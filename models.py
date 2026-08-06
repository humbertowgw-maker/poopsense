import enum
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class PetType(enum.Enum):
    dog = "dog"
    cat = "cat"


class Analysis(db.Model):
    __tablename__ = "analyses"

    id = db.Column(db.Integer, primary_key=True)
    result = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    pet_type = db.Column(
        db.Enum(PetType, name="pet_type_enum", native_enum=True),
        nullable=False,
        default=PetType.dog,
        server_default=PetType.dog.value,
    )

    __table_args__ = (db.Index("ix_analyses_pet_type_created_at", "pet_type", "created_at"),)


class WeeklyPortfolioMetric(db.Model):
    """Aggregate, privacy-preserving weekly usage counters.

    One row per calendar week (UTC, Monday start). No images, no location,
    no per-user data -- just counts, mirroring the retention policy already
    described in `/portfolio-metrics`.
    """

    __tablename__ = "weekly_portfolio_metrics"

    week_start = db.Column(db.String(10), primary_key=True)
    completed_screenings = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    vet_searches = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
